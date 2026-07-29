from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from tvchan.domain.market.model import Adjustment, Bar, BarProvenance, DateRange, Symbol, Timeframe
from tvchan.domain.market.quality import (
    CompletenessStatus,
    QualityPolicy,
    QualityStatus,
)


def _range() -> DateRange:
    return DateRange(datetime(2026, 1, 2, tzinfo=UTC), datetime(2026, 1, 8, tzinfo=UTC))


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
        BarProvenance("fixture", datetime(2026, 1, 1, tzinfo=UTC), f"bar-{day}"),
    )


def test_empty_inputs_follow_the_calendar_status_table() -> None:
    assessment = QualityPolicy().assess(
        range=_range(),
        bars=(),
        same_adjustment_daily_references=(),
        none_daily_factor_bars=(),
        calendar_trade_days=(),
    )

    assert assessment.report.quality is QualityStatus.VALIDATED
    assert assessment.report.completeness is CompletenessStatus.COMPLETE


def test_missing_calendar_preserves_target_and_degrades() -> None:
    target = _bar(date(2026, 1, 2), Adjustment.QFQ)
    assessment = QualityPolicy().assess(
        range=_range(),
        bars=(target,),
        same_adjustment_daily_references=(target,),
        none_daily_factor_bars=(),
        calendar_trade_days=None,
    )

    assert assessment.bars == (target,)
    assert assessment.report.quality is QualityStatus.DEGRADED
    assert assessment.report.completeness is CompletenessStatus.UNKNOWN


def test_calendar_gap_is_reported_without_a_filled_bar() -> None:
    target = _bar(date(2026, 1, 2), Adjustment.QFQ)
    assessment = QualityPolicy().assess(
        range=_range(),
        bars=(target,),
        same_adjustment_daily_references=(target,),
        none_daily_factor_bars=(),
        calendar_trade_days=(date(2026, 1, 2), date(2026, 1, 5)),
    )

    assert assessment.report.completeness is CompletenessStatus.INCOMPLETE
    assert assessment.report.missing_trade_days == (date(2026, 1, 5),)


def test_repair_uses_the_calendar_adjacent_none_bar_only() -> None:
    day = date(2026, 1, 2)
    next_day = date(2026, 1, 5)
    target = _bar(day, Adjustment.QFQ, open="5", high="6", low="4.5", close="5.5", pre_close="5")
    reference = _bar(day, Adjustment.QFQ)
    current_none = _bar(day, Adjustment.NONE, close="10", pre_close="9")
    next_none = _bar(next_day, Adjustment.NONE, close="12", pre_close="20")
    assessment = QualityPolicy().assess(
        range=_range(),
        bars=(target,),
        same_adjustment_daily_references=(reference,),
        none_daily_factor_bars=(current_none, next_none),
        calendar_trade_days=(day, next_day),
    )

    assert assessment.bars == (reference,)
    assert assessment.report.quality is QualityStatus.VALIDATED
    assert assessment.report.mutations[0].factor == Decimal("2")


def test_missing_calendar_adjacent_factor_is_not_replaced_by_a_later_one() -> None:
    day = date(2026, 1, 2)
    next_day = date(2026, 1, 5)
    later_day = date(2026, 1, 6)
    target = _bar(day, Adjustment.QFQ, open="5", high="6", low="4.5", close="5.5", pre_close="5")
    assessment = QualityPolicy().assess(
        range=_range(),
        bars=(target,),
        same_adjustment_daily_references=(_bar(day, Adjustment.QFQ),),
        none_daily_factor_bars=(_bar(day, Adjustment.NONE), _bar(later_day, Adjustment.NONE)),
        calendar_trade_days=(day, next_day, later_day),
    )

    assert assessment.bars == (target,)
    assert assessment.report.messages == ("INSUFFICIENT_REPAIR_EVIDENCE",)


def test_conflicting_identity_is_rejected_before_repair() -> None:
    target = _bar(date(2026, 1, 2), Adjustment.QFQ)
    conflict = _bar(date(2026, 1, 2), Adjustment.QFQ, close="10")
    assessment = QualityPolicy().assess(
        range=_range(),
        bars=(target, conflict),
        same_adjustment_daily_references=(),
        none_daily_factor_bars=(),
        calendar_trade_days=(date(2026, 1, 2),),
    )

    assert assessment.bars == ()
    assert assessment.report.quality is QualityStatus.REJECTED


def test_policy_rejects_invalid_repair_scale() -> None:
    with pytest.raises(ValueError, match="repair_scale"):
        QualityPolicy(True)
