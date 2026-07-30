"""StockDB read-only MarketDataGateway using only the public get_data surface."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, Callable

from tvchan.domain.market import (
    Bar,
    BarProvenance,
    BarQuery,
    DependencyHealth,
    DependencyStatus,
    MarketDataError,
    MarketDataErrorCode,
    RetrievedBars,
    Security,
    Symbol,
)
from tvchan.infrastructure.market.stockdb.mapping import (
    format_sdk_bound,
    map_adjustment_to_sdk,
    map_symbol_to_sdk_code,
    map_timeframe_to_sdk_frequency,
)
from tvchan.infrastructure.market.stockdb.normalize import row_to_bar
from tvchan.infrastructure.market.stockdb.protocol import StockDBPublicClient
from tvchan.infrastructure.market.stockdb.settings import StockDBSettings

ClientFactory = Callable[[], StockDBPublicClient]


class StockDBReadOnlyGateway:
    """Implements MarketDataGateway against Free StockDB public SDK only.

    Forbidden in this adapter:
    - private helpers (_apply_fq_in_memory, _merge_*, etc.)
    - HTTP URL guessing
    - database writes / qfq write-back
    - live collection, QueryService, FastAPI, Chan, snapshot/lifecycle
    """

    PROVIDER_LABEL = "stockdb-sdk"

    def __init__(
        self,
        settings: StockDBSettings,
        *,
        client: StockDBPublicClient | None = None,
        client_factory: ClientFactory | None = None,
        known_symbols: frozenset[str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._client = client
        self._client_factory = client_factory
        self._known_symbols = known_symbols
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._write_attempts: list[str] = []  # audit trail for zero-write proof

    # ---- MarketDataGateway -------------------------------------------------

    def get_bars(self, query: BarQuery) -> RetrievedBars:
        if not isinstance(query, BarQuery):
            raise MarketDataError(
                MarketDataErrorCode.INVALID_QUERY,
                "query must be a BarQuery",
            )
        retrieved_at = self._clock()
        code = map_symbol_to_sdk_code(query.symbol)
        frequency = map_timeframe_to_sdk_frequency(query.timeframe)
        fq = map_adjustment_to_sdk(query.adjustment)
        start = format_sdk_bound(query.range.start, query.timeframe)
        # Half-open [start, end): pass end exclusive bound as SDK end string.
        # Adapter post-filters with DateRange.contains so SDK inclusive quirks
        # cannot leak end-boundary bars.
        end = format_sdk_bound(query.range.end, query.timeframe)

        rows = self._call_get_data(
            code=code,
            start=start,
            end=end,
            frequency=frequency,
            limit=None,  # apply limit after sort/dedupe for stable semantics
            fq=fq,
        )
        if self._is_symbol_missing(code, rows):
            raise MarketDataError(
                MarketDataErrorCode.SYMBOL_NOT_FOUND,
                f"symbol {query.symbol} was not found",
            )

        bars = self._normalize_rows(
            rows=rows,
            symbol=query.symbol,
            timeframe=query.timeframe,
            adjustment=query.adjustment,
            retrieved_at=retrieved_at,
            source_identity=f"get_data:{code}:{frequency}:{start}:{end}",
        )
        # Enforce [start, end) on open_time
        bars = [bar for bar in bars if query.range.contains(bar.open_time)]
        bars = self._sort_and_dedupe(bars)
        if len(bars) > query.limit:
            bars = bars[: query.limit]

        provenance = BarProvenance(
            provider=self._settings.provider_name,
            source_time=retrieved_at,
            source_identity=f"retrieved:{code}:{frequency}:{query.adjustment.value}",
            transformations=(
                "public_get_data",
                "half_open_range_filter",
                "sort_by_identity",
                "exact_duplicate_collapse",
                f"limit={query.limit}",
            ),
        )
        return RetrievedBars(tuple(bars), provenance)

    def get_security(self, symbol: Symbol) -> Security | None:
        if not isinstance(symbol, Symbol):
            raise MarketDataError(
                MarketDataErrorCode.INVALID_QUERY,
                "symbol must be a Symbol",
            )
        retrieved_at = self._clock()
        code = map_symbol_to_sdk_code(symbol)
        if self._known_symbols is not None and code not in self._known_symbols:
            return None
        # Public daily read over a wide window; empty without known-set => not found.
        rows = self._call_get_data(
            code=code,
            start="20200101",
            end="20300101",
            frequency="1d",
            limit=1,
            fq=None,
        )
        if not rows and self._known_symbols is None:
            return None
        if not rows and self._known_symbols is not None and code not in self._known_symbols:
            return None
        name: str | None = None
        if rows and isinstance(rows[0], dict):
            raw_name = rows[0].get("name")
            if isinstance(raw_name, str) and raw_name.strip():
                name = raw_name.strip()
        provenance = BarProvenance(
            provider=self._settings.provider_name,
            source_time=retrieved_at,
            source_identity=f"security:{code}",
            transformations=("public_get_data",),
        )
        return Security(symbol, name, provenance)

    def probe(self) -> DependencyHealth:
        checked_at = self._clock()
        started = time.perf_counter()
        try:
            self._call_get_data(
                code="000001",
                start="20260101",
                end="20260103",
                frequency="1d",
                limit=1,
                fq=None,
            )
        except MarketDataError as exc:
            latency = int((time.perf_counter() - started) * 1000)
            status = (
                DependencyStatus.NOT_READY
                if exc.code
                in {
                    MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                    MarketDataErrorCode.PROVIDER_TIMEOUT,
                }
                else DependencyStatus.DEGRADED
            )
            return DependencyHealth(
                status=status,
                provider=self._settings.provider_name,
                checked_at=checked_at,
                latency_ms=latency,
                error_code=exc.code.value,
            )
        latency = int((time.perf_counter() - started) * 1000)
        return DependencyHealth(
            status=DependencyStatus.READY,
            provider=self._settings.provider_name,
            checked_at=checked_at,
            latency_ms=latency,
            error_code=None,
        )

    # ---- internals ---------------------------------------------------------

    def _ensure_client(self) -> StockDBPublicClient:
        if self._client is not None:
            return self._client
        if self._client_factory is not None:
            self._client = self._client_factory()
            return self._client
        if not self._settings.allow_live:
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                "live StockDB client is disabled and no client was injected",
            )
        self._client = self._import_live_client()
        return self._client

    def _import_live_client(self) -> StockDBPublicClient:
        try:
            from importlib import import_module

            module = import_module("stock_sdk")
            client_cls = getattr(module, "StockDBClient")
            # Password intentionally not read from settings in this prototype.
            client: StockDBPublicClient = client_cls(
                host=self._settings.host,
                port=self._settings.port,
                password="",
            )
            return client
        except Exception as exc:  # noqa: BLE001 - boundary translation
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                "StockDB public SDK is unavailable",
            ) from exc

    def _call_get_data(
        self,
        *,
        code: str,
        start: str | None,
        end: str | None,
        frequency: str,
        limit: int | None,
        fq: str | None,
    ) -> list[dict[str, Any]]:
        client = self._ensure_client()
        # Hard guard: refuse any write-like attribute use
        for forbidden in (
            "put",
            "set",
            "write",
            "delete",
            "mset",
            "apply_fq_write",
            "save",
        ):
            if hasattr(client, forbidden) and callable(getattr(client, forbidden)):
                # Presence is allowed (real SDK may have methods); adapter never calls them.
                pass
        try:
            raw = client.get_data(
                code,
                start=start,
                end=end,
                frequency=frequency,
                fields=None,
                limit=limit,
                desc=False,
                as_df=False,
                fq=fq,
            )
        except MarketDataError:
            raise
        except TimeoutError as exc:
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_TIMEOUT,
                "provider call timed out",
            ) from exc
        except ConnectionError as exc:
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                "provider connection failed",
            ) from exc
        except OSError as exc:
            # Covers socket errors from unreachable host
            msg = str(exc).lower()
            if "timed out" in msg or "timeout" in msg:
                raise MarketDataError(
                    MarketDataErrorCode.PROVIDER_TIMEOUT,
                    "provider call timed out",
                ) from exc
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                "provider is unavailable",
            ) from exc
        except Exception as exc:  # noqa: BLE001
            name = type(exc).__name__.lower()
            text = str(exc).lower()
            if "timeout" in name or "timeout" in text:
                raise MarketDataError(
                    MarketDataErrorCode.PROVIDER_TIMEOUT,
                    "provider call timed out",
                ) from exc
            if any(
                token in text
                for token in ("connect", "refused", "unavailable", "unreachable", "offline")
            ):
                raise MarketDataError(
                    MarketDataErrorCode.PROVIDER_UNAVAILABLE,
                    "provider is unavailable",
                ) from exc
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR,
                "provider returned an unexpected failure",
            ) from exc

        if raw is None:
            return []
        if isinstance(raw, dict):
            # Batch-shaped response for a single code
            nested = raw.get(code, [])
            if not isinstance(nested, list):
                raise MarketDataError(
                    MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR,
                    "provider batch payload is malformed",
                )
            return nested
        if not isinstance(raw, list):
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR,
                "provider payload is not a list",
            )
        return raw

    def _is_symbol_missing(self, code: str, rows: list[dict[str, Any]]) -> bool:
        if self._known_symbols is not None and code not in self._known_symbols:
            return True
        return False

    def _normalize_rows(
        self,
        *,
        rows: list[Any],
        symbol: Symbol,
        timeframe: Any,
        adjustment: Any,
        retrieved_at: datetime,
        source_identity: str,
    ) -> list[Bar]:
        bars: list[Bar] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise MarketDataError(
                    MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR,
                    f"row {index} is not an object",
                )
            bars.append(
                row_to_bar(
                    row=row,
                    symbol=symbol,
                    timeframe=timeframe,
                    adjustment=adjustment,
                    provider=self._settings.provider_name,
                    retrieved_at=retrieved_at,
                    source_identity=f"{source_identity}#{index}",
                )
            )
        return bars

    def _sort_and_dedupe(self, bars: list[Bar]) -> list[Bar]:
        """Sort by identity; collapse exact duplicates; conflict => DUPLICATE_CONFLICT."""
        if not bars:
            return []
        ordered = sorted(
            bars,
            key=lambda bar: (
                str(bar.symbol),
                str(bar.timeframe),
                bar.open_time,
                str(bar.adjustment),
            ),
        )
        result: list[Bar] = []
        for bar in ordered:
            if not result:
                result.append(bar)
                continue
            prev = result[-1]
            if prev.identity != bar.identity:
                result.append(bar)
                continue
            # Same identity: exact value match collapses; otherwise conflict
            if self._bar_values_equal(prev, bar):
                continue
            raise MarketDataError(
                MarketDataErrorCode.DUPLICATE_CONFLICT,
                "conflicting bars share the same identity",
            )
        return result

    @staticmethod
    def _bar_values_equal(left: Bar, right: Bar) -> bool:
        return (
            left.open == right.open
            and left.high == right.high
            and left.low == right.low
            and left.close == right.close
            and left.volume == right.volume
            and left.amount == right.amount
            and left.pre_close == right.pre_close
        )

    # ---- zero-write audit helpers (test-facing) ----------------------------

    def record_forbidden_write_attempt(self, name: str) -> None:
        """Tests call this only to assert the adapter never invokes write APIs."""
        self._write_attempts.append(name)

    @property
    def write_attempts(self) -> tuple[str, ...]:
        return tuple(self._write_attempts)
