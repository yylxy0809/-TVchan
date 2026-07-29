from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest
from tvchan.domain.market import (
    Adjustment,
    Bar,
    BarMutation,
    BarMutationKind,
    BarProvenance,
    BarQuery,
    BarValueSnapshot,
    CompletenessStatus,
    DateRange,
    DependencyHealth,
    DependencyStatus,
    Exchange,
    MarketDataError,
    MarketDataErrorCode,
    QualityReport,
    QualityStatus,
    RetrievedBars,
    Security,
    Symbol,
    Timeframe,
)


@pytest.fixture
def symbol() -> Symbol:
    return Symbol("SSE:600000")


@pytest.fixture
def provenance() -> BarProvenance:
    return BarProvenance(
        provider="stockdb",
        source_time=datetime(2026, 1, 2, 1, tzinfo=UTC),
        source_identity="daily-bars-2026-01-02",
    )


@pytest.fixture
def bar(symbol: Symbol, provenance: BarProvenance) -> Bar:
    return Bar(
        symbol=symbol,
        timeframe=Timeframe.DAY_1,
        open_time=datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
        trading_date=date(2026, 1, 2),
        adjustment=Adjustment.NONE,
        open=Decimal("10.01"),
        high=Decimal("10.50"),
        low=Decimal("9.90"),
        close=Decimal("10.20"),
        volume=Decimal("100"),
        amount=Decimal("1020"),
        pre_close=Decimal("9.95"),
        provenance=provenance,
    )


@pytest.mark.parametrize("value", ("SSE:600000", "SZSE:000001"))
def test_symbol_accepts_canonical_a_share_values(value: str) -> None:
    symbol = Symbol(value)

    assert str(symbol) == value
    assert symbol.exchange in {Exchange.SSE, Exchange.SZSE}
    assert symbol.code == value[-6:]


@pytest.mark.parametrize("value", ("600000", "SH:600000", "SSE:60000", "SSE:6000000", "sse:600000"))
def test_symbol_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(ValueError, match="SSE"):
        Symbol(value)


def test_timeframes_are_exactly_the_frozen_canonical_set() -> None:
    assert {item.value for item in Timeframe} == {
        "1m",
        "5m",
        "15m",
        "30m",
        "60m",
        "1d",
        "1w",
        "1mo",
    }
    with pytest.raises(ValueError):
        Timeframe("1M")


def test_date_range_requires_aware_ordered_boundaries() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)
    interval = DateRange(start, end)

    assert interval.contains(start)
    assert not interval.contains(end)
    with pytest.raises(ValueError, match="timezone-aware"):
        DateRange(start.replace(tzinfo=None), end)
    with pytest.raises(ValueError, match="start < end"):
        DateRange(end, start)


def test_query_requires_positive_integer_limit_and_defaults_to_none(symbol: Symbol) -> None:
    interval = DateRange(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 2, tzinfo=UTC))
    query = BarQuery(symbol, Timeframe.DAY_1, interval, 1)

    assert query.adjustment is Adjustment.NONE
    for limit in (0, -1, True):
        with pytest.raises(ValueError, match="positive integer"):
            BarQuery(symbol, Timeframe.DAY_1, interval, limit)


def test_bar_is_decimal_only_and_enforces_ohlc_identity_and_slots(bar: Bar) -> None:
    assert bar.identity == (bar.symbol, bar.timeframe, bar.open_time, bar.adjustment)
    assert "__dict__" not in dir(bar)
    with pytest.raises(FrozenInstanceError):
        bar.close = Decimal("10.30")  # type: ignore[misc]
    with pytest.raises(TypeError, match="Decimal"):
        Bar(
            bar.symbol,
            bar.timeframe,
            bar.open_time,
            bar.trading_date,
            bar.adjustment,
            Decimal("10"),
            Decimal("11"),
            Decimal("9"),
            10.5,  # type: ignore[arg-type]
            None,
            None,
            None,
            bar.provenance,
        )
    with pytest.raises(ValueError, match="OHLC"):
        Bar(
            bar.symbol,
            bar.timeframe,
            bar.open_time,
            bar.trading_date,
            bar.adjustment,
            Decimal("10"),
            Decimal("11"),
            Decimal("10.5"),
            Decimal("9"),
            None,
            None,
            None,
            bar.provenance,
        )


def test_bar_requires_shanghai_trading_date_and_opening_time(bar: Bar) -> None:
    with pytest.raises(ValueError, match="trading_date"):
        Bar(
            bar.symbol,
            bar.timeframe,
            bar.open_time,
            date(2026, 1, 3),
            bar.adjustment,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.amount,
            bar.pre_close,
            bar.provenance,
        )
    intraday = Bar(
        bar.symbol,
        Timeframe.MINUTE_1,
        datetime(2026, 1, 2, 2, tzinfo=UTC),
        date(2026, 1, 2),
        bar.adjustment,
        bar.open,
        bar.high,
        bar.low,
        bar.close,
        bar.volume,
        bar.amount,
        None,
        bar.provenance,
    )
    assert intraday.timeframe is Timeframe.MINUTE_1


def test_provenance_and_security_contain_only_safe_identifying_fields(
    symbol: Symbol, provenance: BarProvenance
) -> None:
    security = Security(symbol, None, provenance)
    assert tuple(field.name for field in fields(security)) == ("symbol", "name", "provenance")
    with pytest.raises(ValueError, match="credentials or a URL"):
        BarProvenance("stockdb", datetime(2026, 1, 1, tzinfo=UTC), "https://user:secret@host")


def test_retrieved_bars_require_canonical_sort_order(bar: Bar, provenance: BarProvenance) -> None:
    later = Bar(
        bar.symbol,
        bar.timeframe,
        datetime(2026, 1, 3, 1, 30, tzinfo=UTC),
        date(2026, 1, 3),
        bar.adjustment,
        bar.open,
        bar.high,
        bar.low,
        bar.close,
        bar.volume,
        bar.amount,
        bar.pre_close,
        provenance,
    )
    assert RetrievedBars((bar, later), provenance).bars == (bar, later)
    with pytest.raises(ValueError, match="sorted"):
        RetrievedBars((later, bar), provenance)


def test_quality_dtos_are_frozen_and_keep_separate_states() -> None:
    report = QualityReport(QualityStatus.DEGRADED, CompletenessStatus.UNKNOWN)
    assert report.quality is QualityStatus.DEGRADED
    assert report.completeness is CompletenessStatus.UNKNOWN
    with pytest.raises(FrozenInstanceError):
        report.quality = QualityStatus.VALIDATED  # type: ignore[misc]


@pytest.mark.parametrize(
    ("code", "retryable"),
    [
        (MarketDataErrorCode.INVALID_QUERY, False),
        (MarketDataErrorCode.UNSUPPORTED_TIMEFRAME, False),
        (MarketDataErrorCode.SYMBOL_NOT_FOUND, False),
        (MarketDataErrorCode.PROVIDER_UNAVAILABLE, True),
        (MarketDataErrorCode.PROVIDER_TIMEOUT, True),
        (MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR, False),
        (MarketDataErrorCode.NORMALIZATION_ERROR, False),
        (MarketDataErrorCode.DUPLICATE_CONFLICT, False),
    ],
)
def test_error_code_retryability_is_stable(code: MarketDataErrorCode, retryable: bool) -> None:
    error = MarketDataError(code, "safe detail")

    assert error.retryable is retryable
    assert error.code is code


@pytest.mark.parametrize("value", ("NaN", "sNaN", "Infinity", "-Infinity"))
def test_bar_rejects_non_finite_decimals_without_decimal_leaks(bar: Bar, value: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        Bar(
            bar.symbol,
            bar.timeframe,
            bar.open_time,
            bar.trading_date,
            bar.adjustment,
            Decimal(value),
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.amount,
            bar.pre_close,
            bar.provenance,
        )


def test_value_objects_reject_runtime_type_impostors(bar: Bar, provenance: BarProvenance) -> None:
    interval = DateRange(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 2, tzinfo=UTC))
    with pytest.raises(TypeError, match="Symbol"):
        BarQuery(cast(Symbol, "SSE:600000"), Timeframe.DAY_1, interval, 1)
    with pytest.raises(TypeError, match="Timeframe"):
        BarQuery(bar.symbol, cast(Timeframe, "1d"), interval, 1)
    with pytest.raises(TypeError, match="Adjustment"):
        BarQuery(bar.symbol, Timeframe.DAY_1, interval, 1, cast(Adjustment, "NONE"))
    with pytest.raises(TypeError, match="Symbol"):
        Security(cast(Symbol, "SSE:600000"), None, provenance)
    with pytest.raises(TypeError, match="DependencyStatus"):
        DependencyHealth(
            cast(DependencyStatus, "READY"),
            "stockdb",
            datetime(2026, 1, 1, tzinfo=UTC),
            5,
        )


def test_nested_collections_must_be_immutable_tuples(bar: Bar, provenance: BarProvenance) -> None:
    with pytest.raises(TypeError, match="tuple"):
        BarProvenance(
            "stockdb", datetime(2026, 1, 1, tzinfo=UTC), "fixture", cast(tuple[str, ...], [])
        )
    with pytest.raises(TypeError, match="tuple"):
        RetrievedBars(cast(tuple[Bar, ...], [bar]), provenance)
    with pytest.raises(TypeError, match="tuple"):
        QualityReport(
            QualityStatus.DEGRADED,
            CompletenessStatus.UNKNOWN,
            cast(tuple[BarMutation, ...], []),
        )


def test_safe_text_rejects_blank_and_sensitive_values() -> None:
    with pytest.raises(ValueError, match="safe"):
        BarProvenance(" ", datetime(2026, 1, 1, tzinfo=UTC), "fixture")
    with pytest.raises(ValueError, match="safe"):
        BarProvenance("stockdb", datetime(2026, 1, 1, tzinfo=UTC), "token=secret")
    with pytest.raises(ValueError, match="safe"):
        MarketDataError(MarketDataErrorCode.INVALID_QUERY, " https://user:password@example.test ")


def _snapshot() -> BarValueSnapshot:
    return BarValueSnapshot(
        Decimal("10"),
        Decimal("11"),
        Decimal("9"),
        Decimal("10.5"),
        Decimal("1"),
        None,
        Decimal("9.5"),
    )


def _identity(symbol: Symbol) -> tuple[Symbol, Timeframe, datetime, Adjustment]:
    return (symbol, Timeframe.DAY_1, datetime(2026, 1, 2, 1, 30, tzinfo=UTC), Adjustment.NONE)


def test_bar_value_snapshot_is_frozen_and_enforces_bar_numeric_contract() -> None:
    snapshot = _snapshot()
    assert "__dict__" not in dir(snapshot)
    with pytest.raises(FrozenInstanceError):
        snapshot.close = Decimal("10")  # type: ignore[misc]
    for value in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
        with pytest.raises(ValueError, match="finite"):
            BarValueSnapshot(value, Decimal("11"), Decimal("9"), Decimal("10"), None, None, None)
    with pytest.raises(ValueError, match="OHLC"):
        BarValueSnapshot(
            Decimal("10"), Decimal("11"), Decimal("10.5"), Decimal("9"), None, None, None
        )
    with pytest.raises(ValueError, match="non-negative"):
        BarValueSnapshot(
            Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), Decimal("-1"), None, None
        )
    with pytest.raises(ValueError, match="positive"):
        BarValueSnapshot(
            Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), None, None, Decimal("0")
        )


def test_repaired_mutation_requires_complete_provenance(symbol: Symbol) -> None:
    identity = _identity(symbol)
    snapshot = _snapshot()
    mutation = BarMutation(
        BarMutationKind.REPAIRED,
        identity,
        "daily factor repair",
        Decimal("1.1"),
        snapshot,
        snapshot,
        identity,
        2,
    )
    assert mutation.factor == Decimal("1.1")
    for field in range(4, 9):
        values: list[object] = [Decimal("1.1"), snapshot, snapshot, identity, 2]
        values[field - 4] = None
        with pytest.raises(ValueError, match="REPAIRED"):
            BarMutation(BarMutationKind.REPAIRED, identity, "repair", *values)  # type: ignore[arg-type]


def test_dropped_mutation_has_before_and_no_after(symbol: Symbol) -> None:
    identity = _identity(symbol)
    snapshot = _snapshot()
    assert (
        BarMutation(BarMutationKind.DROPPED, identity, "invalid bar", before=snapshot).before
        is snapshot
    )
    with pytest.raises(ValueError, match="DROPPED"):
        BarMutation(BarMutationKind.DROPPED, identity, "drop")
    with pytest.raises(ValueError, match="DROPPED"):
        BarMutation(BarMutationKind.DROPPED, identity, "drop", before=snapshot, after=snapshot)


def test_mutation_rejects_invalid_provenance_values(symbol: Symbol) -> None:
    identity = _identity(symbol)
    snapshot = _snapshot()
    for factor in (Decimal("NaN"), Decimal("Infinity"), cast(Decimal, "1")):
        with pytest.raises((TypeError, ValueError)):
            BarMutation(BarMutationKind.DROPPED, identity, "drop", factor=factor, before=snapshot)

    class IntSubclass(int):
        pass

    assert (
        BarMutation(BarMutationKind.DROPPED, identity, "drop", before=snapshot, scale=None).scale
        is None
    )
    assert (
        BarMutation(BarMutationKind.DROPPED, identity, "drop", before=snapshot, scale=1).scale == 1
    )
    for scale in (True, IntSubclass(1), -1, cast(int, "1")):
        with pytest.raises(ValueError, match="scale"):
            BarMutation(BarMutationKind.DROPPED, identity, "drop", before=snapshot, scale=scale)
    for invalid_identity in (
        ("SSE:600000", Timeframe.DAY_1, identity[2], Adjustment.NONE),
        (symbol, Timeframe.DAY_1, datetime(2026, 1, 2, 1, 30), Adjustment.NONE),
        (symbol, Timeframe.DAY_1, identity[2]),
    ):
        with pytest.raises(TypeError, match="identity"):
            BarMutation(
                BarMutationKind.DROPPED,
                cast(tuple[Symbol, Timeframe, datetime, Adjustment], invalid_identity),
                "drop",
                before=snapshot,
            )
    with pytest.raises(ValueError, match="safe"):
        BarMutation(BarMutationKind.DROPPED, identity, "https://token@host", before=snapshot)
    with pytest.raises(TypeError, match="identity"):
        BarMutation(
            BarMutationKind.DROPPED,
            identity,
            "drop",
            before=snapshot,
            reference_identity=(symbol, Timeframe.DAY_1, datetime(2026, 1, 2), Adjustment.NONE),
        )
    with pytest.raises(TypeError, match="BarValueSnapshot"):
        BarMutation(
            BarMutationKind.DROPPED, identity, "drop", before=cast(BarValueSnapshot, object())
        )
    with pytest.raises(TypeError, match="BarValueSnapshot"):
        BarMutation(
            BarMutationKind.DROPPED,
            identity,
            "drop",
            before=snapshot,
            after=cast(BarValueSnapshot, object()),
        )


def test_quality_report_carries_multiple_immutable_mutations(symbol: Symbol) -> None:
    identity = _identity(symbol)
    snapshot = _snapshot()
    mutations = (
        BarMutation(BarMutationKind.DROPPED, identity, "drop", before=snapshot),
        BarMutation(BarMutationKind.DROPPED, identity, "drop again", before=snapshot),
    )
    report = QualityReport(QualityStatus.DEGRADED, CompletenessStatus.INCOMPLETE, mutations)
    assert report.mutations == mutations
    with pytest.raises(TypeError, match="tuple"):
        QualityReport(
            QualityStatus.DEGRADED, CompletenessStatus.INCOMPLETE, cast(tuple[BarMutation, ...], [])
        )


def test_dependency_health_is_frozen_and_safe() -> None:
    health = DependencyHealth(
        DependencyStatus.READY,
        "stockdb",
        datetime(2026, 1, 1, tzinfo=UTC),
        5,
    )
    assert health.status is DependencyStatus.READY
    with pytest.raises(ValueError, match="safe"):
        DependencyHealth(
            DependencyStatus.NOT_READY,
            "https://token@host",
            datetime(2026, 1, 1, tzinfo=UTC),
            None,
        )
