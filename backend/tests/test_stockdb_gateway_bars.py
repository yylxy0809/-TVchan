from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from tvchan.domain.market import (
    Adjustment,
    BarQuery,
    DateRange,
    MarketDataError,
    MarketDataErrorCode,
    Symbol,
    Timeframe,
)
from tvchan.domain.market.model import SHANGHAI
from tvchan.infrastructure.market.stockdb import (
    FakeStockDBPublicClient,
    StockDBReadOnlyGateway,
    StockDBSettings,
)


def test_get_bars_maps_decimal_and_shanghai_aware_open_time(
    gateway: StockDBReadOnlyGateway, daily_query: BarQuery
) -> None:
    result = gateway.get_bars(daily_query)
    assert len(result.bars) >= 1
    bar = result.bars[0]
    assert isinstance(bar.open, Decimal)
    assert isinstance(bar.close, Decimal)
    assert bar.open_time.tzinfo is not None
    assert bar.open_time.utcoffset() is not None
    assert bar.open_time.astimezone(SHANGHAI).hour == 9
    assert bar.open_time.astimezone(SHANGHAI).minute == 30
    assert bar.trading_date.isoformat() == "2026-01-02"
    assert bar.adjustment is Adjustment.NONE


def test_half_open_range_excludes_end_boundary(gateway: StockDBReadOnlyGateway) -> None:
    # Range ends at 2026-01-06 09:30 Shanghai => end exclusive excludes 2026-01-06 bar
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 6, 1, 30, tzinfo=UTC),
        ),
        limit=100,
        adjustment=Adjustment.NONE,
    )
    result = gateway.get_bars(query)
    dates = [bar.trading_date.isoformat() for bar in result.bars]
    assert "2026-01-02" in dates
    assert "2026-01-05" in dates
    assert "2026-01-06" not in dates


def test_limit_applied_after_sort(gateway: StockDBReadOnlyGateway) -> None:
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 10, 1, 30, tzinfo=UTC),
        ),
        limit=2,
        adjustment=Adjustment.NONE,
    )
    result = gateway.get_bars(query)
    assert len(result.bars) == 2
    assert result.bars[0].open_time < result.bars[1].open_time


def test_bars_are_sorted_by_identity(
    gateway: StockDBReadOnlyGateway, daily_query: BarQuery
) -> None:
    result = gateway.get_bars(daily_query)
    keys = [(str(b.symbol), str(b.timeframe), b.open_time, str(b.adjustment)) for b in result.bars]
    assert keys == sorted(keys)


def test_exact_duplicate_rows_collapse(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, known_codes={"600000", "000001"})
    # Inject exact duplicate into the next response by monkeypatching get_data
    original = client.get_data

    def with_dup(*args: Any, **kwargs: Any) -> Any:
        rows = original(*args, **kwargs)
        if rows:
            rows = list(rows) + [dict(rows[0])]
        return rows

    client.get_data = with_dup  # type: ignore[method-assign]
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000", "000001"}),
        clock=lambda: fixed_clock,
    )
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 3, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    result = gateway.get_bars(query)
    assert len(result.bars) == 1


def test_conflicting_duplicate_raises(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, known_codes={"600000", "000001"})
    original = client.get_data

    def with_conflict(*args: Any, **kwargs: Any) -> Any:
        rows = original(*args, **kwargs)
        if rows:
            conflict = dict(rows[0])
            # Keep OHLC valid; conflict on volume (same identity, different values).
            conflict["volume"] = "999999"
            rows = list(rows) + [conflict]
        return rows

    client.get_data = with_conflict  # type: ignore[method-assign]
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000", "000001"}),
        clock=lambda: fixed_clock,
    )
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
        gateway.get_bars(query)
    assert exc.value.code is MarketDataErrorCode.DUPLICATE_CONFLICT
    assert not exc.value.retryable


def test_empty_result_is_empty_not_error(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, known_codes={"600000", "000001"})
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000", "000001"}),
        clock=lambda: fixed_clock,
    )
    # Range outside fixture data for known symbol
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2025, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2025, 1, 3, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    result = gateway.get_bars(query)
    assert result.bars == ()


def test_minute_bars_preserve_shanghai_wall_time(gateway: StockDBReadOnlyGateway) -> None:
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.MINUTE_30,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 2, 3, 0, tzinfo=UTC),
        ),
        limit=10,
        adjustment=Adjustment.NONE,
    )
    result = gateway.get_bars(query)
    assert len(result.bars) >= 1
    first = result.bars[0]
    local = first.open_time.astimezone(SHANGHAI)
    assert local.hour == 9 and local.minute == 30
    assert first.pre_close is None


def test_adjustment_qfq_passed_to_public_fq_parameter(
    gateway: StockDBReadOnlyGateway, fake_client: FakeStockDBPublicClient
) -> None:
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 7, 1, 30, tzinfo=UTC),
        ),
        limit=10,
        adjustment=Adjustment.QFQ,
    )
    result = gateway.get_bars(query)
    assert fake_client.calls[-1]["fq"] == "qfq"
    assert all(bar.adjustment is Adjustment.QFQ for bar in result.bars)


def test_month_timeframe_maps_to_sdk_1M(
    gateway: StockDBReadOnlyGateway, fake_client: FakeStockDBPublicClient
) -> None:
    query = BarQuery(
        Symbol("SSE:600000"),
        Timeframe.MONTH_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 2, 2, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    gateway.get_bars(query)
    assert fake_client.calls[-1]["frequency"] == "1M"


def test_provenance_is_present_and_safe(
    gateway: StockDBReadOnlyGateway, daily_query: BarQuery
) -> None:
    result = gateway.get_bars(daily_query)
    assert result.provenance.provider == "stockdb-sdk-fixture"
    assert result.provenance.source_time.tzinfo is not None
    assert "public_get_data" in result.provenance.transformations
    assert "://" not in result.provenance.source_identity
    assert result.bars
    assert result.bars[0].provenance.provider == "stockdb-sdk-fixture"
