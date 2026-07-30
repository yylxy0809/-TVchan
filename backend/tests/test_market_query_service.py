"""Offline MarketDataQueryService vertical tests (T110 C003)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from tvchan.application.market import (
    MarketDataQueryResult,
    MarketDataQueryService,
    QueryLimits,
)
from tvchan.application.ports import MarketDataGateway, TradingCalendarPort
from tvchan.domain.market import (
    Adjustment,
    Bar,
    BarProvenance,
    BarQuery,
    CompletenessStatus,
    DateRange,
    DependencyHealth,
    MarketDataError,
    MarketDataErrorCode,
    QualityStatus,
    RetrievedBars,
    Security,
    Symbol,
    Timeframe,
)
from tvchan.infrastructure.market.static_trading_calendar import (
    StaticTradingCalendarAdapter,
    StaticTradingCalendarSnapshot,
)
from tvchan.infrastructure.market.stockdb import (
    FakeStockDBPublicClient,
    StockDBReadOnlyGateway,
    StockDBSettings,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "stockdb" / "bars_600000.json"
FIXED = datetime(2026, 1, 8, 2, 0, 0, tzinfo=UTC)


def _settings() -> StockDBSettings:
    return StockDBSettings(
        host="127.0.0.1",
        port=7899,
        timeout_ms=1000,
        provider_name="stockdb-sdk-fixture",
        allow_live=False,
    )


def _gateway(*, fault: str = "none") -> StockDBReadOnlyGateway:
    client = FakeStockDBPublicClient(
        FIXTURE,
        fault=fault,  # type: ignore[arg-type]
        known_codes={"600000", "000001"},
    )
    return StockDBReadOnlyGateway(
        _settings(),
        client=client,
        known_symbols=frozenset({"600000", "000001"}),
        clock=lambda: FIXED,
    )


def _calendar(days: tuple[date, ...]) -> StaticTradingCalendarAdapter:
    snap = StaticTradingCalendarSnapshot("2026-01-01", "Asia/Shanghai", days)
    return StaticTradingCalendarAdapter((snap,), "2026-01-01")


def _daily_query(*, limit: int = 100, end_day: int = 7) -> BarQuery:
    return BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, end_day, 1, 30, tzinfo=UTC),
        ),
        limit=limit,
        adjustment=Adjustment.NONE,
    )


def _bar(
    day: date,
    adjustment: Adjustment,
    *,
    open: str = "10.0000",
    high: str = "12.0000",
    low: str = "9.0000",
    close: str = "11.0000",
    pre_close: str | None = "10.0000",
) -> Bar:
    return Bar(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        datetime(day.year, day.month, day.day, 1, 30, tzinfo=UTC),
        day,
        adjustment,
        Decimal(open),
        Decimal(high),
        Decimal(low),
        Decimal(close),
        Decimal("10"),
        Decimal("110"),
        Decimal(pre_close) if pre_close is not None else None,
        BarProvenance("fixture", FIXED, f"bar-{day}-{adjustment.value}"),
    )


def test_query_limits_rejects_before_any_gateway_io() -> None:
    calls: list[str] = []

    class CountingGateway:
        def get_bars(self, query: BarQuery) -> RetrievedBars:
            calls.append("get_bars")
            raise AssertionError("gateway must not be called after limit rejection")

        def get_security(self, symbol: Symbol) -> Security | None:
            calls.append("get_security")
            return None

        def probe(self) -> DependencyHealth:
            calls.append("probe")
            raise AssertionError("probe must not run")

    class CountingCalendar:
        def list_trade_days(self, range: DateRange) -> tuple[date, ...]:
            calls.append("list_trade_days")
            return ()

    service = MarketDataQueryService(
        cast(MarketDataGateway, CountingGateway()),
        cast(TradingCalendarPort, CountingCalendar()),
        limits=QueryLimits(max_limit=10),
    )
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(datetime(2026, 1, 2, tzinfo=UTC), datetime(2026, 1, 8, tzinfo=UTC)),
        limit=11,
    )
    with pytest.raises(MarketDataError) as exc:
        service.query_bars(query)
    assert exc.value.code is MarketDataErrorCode.INVALID_QUERY
    assert calls == []


def test_daily_none_validated_complete_with_matching_references() -> None:
    gateway = _gateway()
    # Fixture has 20260102, 05, 06, 07 daily; half-open end at 01-07 09:30 excludes 07
    calendar = _calendar((date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6)))
    # QualityPolicy NONE path requires full Bar equality (incl. provenance).
    # Deterministic fixture + fixed clock => two get_bars calls yield equal bars.
    retrieved = gateway.get_bars(_daily_query())
    service = MarketDataQueryService(
        gateway,
        calendar,
        same_adjustment_daily_references=retrieved.bars,
        none_daily_factor_bars=(),
    )
    result = service.query_bars(_daily_query())
    assert isinstance(result, MarketDataQueryResult)
    assert len(result.bars) == 3
    assert result.report.quality is QualityStatus.VALIDATED
    assert result.report.completeness is CompletenessStatus.COMPLETE
    assert result.report.missing_trade_days == ()
    assert result.retrieval_provenance.provider == "stockdb-sdk-fixture"
    assert "public_get_data" in result.retrieval_provenance.transformations
    # sorted
    times = [bar.open_time for bar in result.bars]
    assert times == sorted(times)


def test_half_open_range_and_limit_via_service() -> None:
    gateway = _gateway()
    # end exclusive at 2026-01-06 09:30 excludes 01-06
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 6, 1, 30, tzinfo=UTC),
        ),
        limit=2,
        adjustment=Adjustment.NONE,
    )
    retrieved = gateway.get_bars(query)
    calendar = _calendar((date(2026, 1, 2), date(2026, 1, 5)))
    service = MarketDataQueryService(
        gateway,
        calendar,
        same_adjustment_daily_references=retrieved.bars,
    )
    result = service.query_bars(query)
    dates = [bar.trading_date for bar in result.bars]
    assert date(2026, 1, 6) not in dates
    assert len(result.bars) == 2
    assert result.bars[0].open_time < result.bars[1].open_time


def test_daily_incomplete_when_calendar_has_gap() -> None:
    gateway = _gateway()
    # 2026-01-03 is inside the half-open query window but absent from fixture bars.
    calendar = _calendar((date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 5), date(2026, 1, 6)))
    retrieved = gateway.get_bars(_daily_query())
    service = MarketDataQueryService(
        gateway,
        calendar,
        same_adjustment_daily_references=retrieved.bars,
    )
    result = service.query_bars(_daily_query())
    assert result.report.completeness is CompletenessStatus.INCOMPLETE
    assert date(2026, 1, 3) in result.report.missing_trade_days
    # qualified bars still present => gap alone is not DEGRADED when bars exist
    assert result.report.quality is QualityStatus.VALIDATED
    assert result.bars


def test_daily_degraded_when_references_missing() -> None:
    gateway = _gateway()
    calendar = _calendar((date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6)))
    service = MarketDataQueryService(
        gateway,
        calendar,
        same_adjustment_daily_references=(),  # no injected references
    )
    result = service.query_bars(_daily_query())
    assert result.report.quality is QualityStatus.DEGRADED
    assert "MISSING_SAME_ADJUSTMENT_REFERENCE" in result.report.messages
    assert result.bars  # preserved


def test_daily_unknown_completeness_without_calendar_days_in_range() -> None:
    """Empty calendar tuple is known empty (COMPLETE if no bars expected elsewhere).

    QualityPolicy treats calendar_trade_days=None as UNKNOWN; the service always
    supplies the port result. Empty trade days with empty bars => VALIDATED/COMPLETE.
    """
    gateway = _gateway()
    calendar = _calendar(())  # no trade days in any range
    service = MarketDataQueryService(gateway, calendar, same_adjustment_daily_references=())
    # Query outside fixture so bars empty
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2025, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2025, 1, 3, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    result = service.query_bars(query)
    assert result.bars == ()
    assert result.report.quality is QualityStatus.VALIDATED
    assert result.report.completeness is CompletenessStatus.COMPLETE


def test_qfq_repair_uses_only_injected_references_no_second_provider_query() -> None:
    """QFQ discontinuity repair is driven solely by injected bars — no gateway re-query."""
    day = date(2026, 1, 2)
    next_day = date(2026, 1, 5)
    # Provider returns a broken QFQ bar for the day (values that will be repaired).
    broken = {
        "date": "20260102",
        "code": "600000",
        "name": "SPDB",
        "open": "5",
        "high": "6",
        "low": "4.5",
        "close": "5.5",
        "volume": "1000",
        "amount": "10200",
        "pre_close": "5",
    }

    class OneShotClient:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []
            self.write_calls: list[str] = []

        def get_data(
            self,
            code: str | list[str],
            start: str | None = None,
            end: str | None = None,
            frequency: str = "1d",
            fields: str | list[str] | None = None,
            limit: int | None = None,
            desc: bool = False,
            as_df: bool = False,
            fq: str | None = "qfq",
        ) -> Any:
            self.calls.append({"code": code, "start": start, "end": end, "frequency": frequency})
            if frequency == "1d" and code == "600000":
                return [broken]
            return []

    client = OneShotClient()
    gateway = StockDBReadOnlyGateway(
        _settings(),
        client=client,
        known_symbols=frozenset({"600000"}),
        clock=lambda: FIXED,
    )
    calendar = _calendar((day, next_day))
    reference = _bar(day, Adjustment.QFQ)
    current_none = _bar(day, Adjustment.NONE, close="10", pre_close="9")
    next_none = _bar(next_day, Adjustment.NONE, close="12", pre_close="20")
    service = MarketDataQueryService(
        gateway,
        calendar,
        same_adjustment_daily_references=(reference,),
        none_daily_factor_bars=(current_none, next_none),
    )
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 6, 1, 30, tzinfo=UTC),
        ),
        limit=10,
        adjustment=Adjustment.QFQ,
    )
    result = service.query_bars(query)
    assert result.report.quality is QualityStatus.VALIDATED
    assert result.bars[0].close == Decimal("11.0000")
    assert result.report.mutations and result.report.mutations[0].factor == Decimal("2")
    # Exactly one provider get_data for the target query — no repair re-query.
    assert len(client.calls) == 1


def test_rejected_when_conflicting_targets_injected_as_duplicates_from_gateway() -> None:
    """Gateway raises DUPLICATE_CONFLICT before quality; typed error surfaces."""
    client = FakeStockDBPublicClient(FIXTURE, known_codes={"600000"})
    original = client.get_data

    def with_conflict(*args: Any, **kwargs: Any) -> Any:
        rows = original(*args, **kwargs)
        if rows:
            conflict = dict(rows[0])
            conflict["volume"] = "999999"
            rows = list(rows) + [conflict]
        return rows

    client.get_data = with_conflict  # type: ignore[method-assign]
    gateway = StockDBReadOnlyGateway(
        _settings(),
        client=client,
        known_symbols=frozenset({"600000"}),
        clock=lambda: FIXED,
    )
    service = MarketDataQueryService(gateway, _calendar((date(2026, 1, 2),)))
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 3, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    with pytest.raises(MarketDataError) as exc:
        service.query_bars(query)
    assert exc.value.code is MarketDataErrorCode.DUPLICATE_CONFLICT


def test_quality_rejected_on_conflicting_injected_references() -> None:
    gateway = _gateway()
    calendar = _calendar((date(2026, 1, 2),))
    target_ref = _bar(date(2026, 1, 2), Adjustment.NONE)
    conflict_ref = _bar(date(2026, 1, 2), Adjustment.NONE, close="10")
    # Force gateway to return empty so assess sees only reference conflict path:
    # Actually need non-empty bars with conflict in references.
    retrieved = gateway.get_bars(
        BarQuery(
            Symbol("SSE:600000"),
            Timeframe.DAY_1,
            DateRange(
                datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
                datetime(2026, 1, 3, 1, 30, tzinfo=UTC),
            ),
            limit=10,
        )
    )
    service = MarketDataQueryService(
        gateway,
        calendar,
        same_adjustment_daily_references=(target_ref, conflict_ref),
    )
    result = service.query_bars(
        BarQuery(
            Symbol("SSE:600000"),
            Timeframe.DAY_1,
            DateRange(
                datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
                datetime(2026, 1, 3, 1, 30, tzinfo=UTC),
            ),
            limit=10,
        )
    )
    assert retrieved.bars  # fixture has the day
    assert result.report.quality is QualityStatus.REJECTED
    assert result.bars == ()
    assert result.report.completeness is CompletenessStatus.UNKNOWN


def test_minute_30_and_5_passthrough_unknown_completeness() -> None:
    gateway = _gateway()
    calendar = _calendar((date(2026, 1, 2),))
    service = MarketDataQueryService(gateway, calendar)
    for tf in (Timeframe.MINUTE_30, Timeframe.MINUTE_5):
        query = BarQuery(
            Symbol("SSE:600000"),
            tf,
            DateRange(
                datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
                datetime(2026, 1, 2, 3, 0, tzinfo=UTC),
            ),
            limit=10,
        )
        result = service.query_bars(query)
        if tf is Timeframe.MINUTE_30:
            assert len(result.bars) >= 1
            assert result.bars[0].open_time.astimezone(UTC).hour == 1  # 09:30 Shanghai
        # 5m may be empty in fixture — empty is not an error
        assert result.report.quality is QualityStatus.VALIDATED
        assert result.report.completeness is CompletenessStatus.UNKNOWN
        assert "NON_DAILY_QUALITY_PASSTHROUGH" in result.report.messages
        assert result.retrieval_provenance.provider == "stockdb-sdk-fixture"


def test_provider_unavailable_typed_error() -> None:
    gateway = _gateway(fault="unavailable")
    service = MarketDataQueryService(gateway, _calendar(()))
    with pytest.raises(MarketDataError) as exc:
        service.query_bars(_daily_query())
    assert exc.value.code is MarketDataErrorCode.PROVIDER_UNAVAILABLE
    assert exc.value.retryable


def test_symbol_not_found_typed_error() -> None:
    gateway = _gateway()
    service = MarketDataQueryService(gateway, _calendar(()))
    query = BarQuery(
        Symbol("SSE:600519"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 7, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    with pytest.raises(MarketDataError) as exc:
        service.query_bars(query)
    assert exc.value.code is MarketDataErrorCode.SYMBOL_NOT_FOUND


def test_query_limits_default_accepts_reasonable_limit() -> None:
    limits = QueryLimits()
    limits.enforce(_daily_query(limit=100))
    with pytest.raises(ValueError):
        QueryLimits(max_limit=0)


def test_empty_bars_with_known_calendar_degraded_incomplete() -> None:
    gateway = _gateway()
    calendar = _calendar((date(2025, 1, 2), date(2025, 1, 3)))
    service = MarketDataQueryService(gateway, calendar)
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2025, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2025, 1, 6, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    result = service.query_bars(query)
    assert result.bars == ()
    assert result.report.quality is QualityStatus.DEGRADED
    assert result.report.completeness is CompletenessStatus.INCOMPLETE
