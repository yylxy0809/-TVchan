"""Immutable quality and completeness result vocabulary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Context, Decimal
from enum import StrEnum

from tvchan.domain.market.model import (
    SHANGHAI,
    Adjustment,
    Bar,
    BarIdentity,
    DateRange,
    Symbol,
    Timeframe,
)


class QualityStatus(StrEnum):
    VALIDATED = "VALIDATED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"


class CompletenessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class BarMutationKind(StrEnum):
    REPAIRED = "REPAIRED"
    DROPPED = "DROPPED"


def _require_decimal(name: str, value: Decimal | None, *, positive: bool) -> None:
    if value is None:
        return
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if not positive and value < 0:
        raise ValueError(f"{name} must be non-negative")


def _require_identity(name: str, identity: object) -> None:
    if not isinstance(identity, tuple) or len(identity) != 4:
        raise TypeError(f"{name} must be a BarIdentity tuple")
    symbol, timeframe, open_time, adjustment = identity
    if (
        not isinstance(symbol, Symbol)
        or not isinstance(timeframe, Timeframe)
        or not isinstance(open_time, datetime)
        or open_time.tzinfo is None
        or open_time.utcoffset() is None
        or not isinstance(adjustment, Adjustment)
    ):
        raise TypeError(f"{name} must be a valid BarIdentity")


def _require_safe_reason(reason: str) -> None:
    forbidden = ("://", "@", "credential", "password", "secret", "token")
    if (
        not isinstance(reason, str)
        or not reason.strip()
        or any(part in reason.lower() for part in forbidden)
    ):
        raise ValueError("reason must be safe text without credentials or a URL")


@dataclass(frozen=True, slots=True)
class BarValueSnapshot:
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    amount: Decimal | None
    pre_close: Decimal | None

    def __post_init__(self) -> None:
        for name, value in (
            ("open", self.open),
            ("high", self.high),
            ("low", self.low),
            ("close", self.close),
        ):
            _require_decimal(name, value, positive=True)
        _require_decimal("volume", self.volume, positive=False)
        _require_decimal("amount", self.amount, positive=False)
        _require_decimal("pre_close", self.pre_close, positive=True)
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError(
                "OHLC values must satisfy low <= min(open, close) <= max(open, close) <= high"
            )


@dataclass(frozen=True, slots=True)
class BarMutation:
    kind: BarMutationKind
    identity: BarIdentity
    reason: str
    factor: Decimal | None = None
    before: BarValueSnapshot | None = None
    after: BarValueSnapshot | None = None
    reference_identity: BarIdentity | None = None
    scale: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, BarMutationKind):
            raise TypeError("kind must be BarMutationKind")
        _require_identity("identity", self.identity)
        _require_safe_reason(self.reason)
        _require_decimal("factor", self.factor, positive=True)
        if self.before is not None and not isinstance(self.before, BarValueSnapshot):
            raise TypeError("before must be BarValueSnapshot")
        if self.after is not None and not isinstance(self.after, BarValueSnapshot):
            raise TypeError("after must be BarValueSnapshot")
        if self.reference_identity is not None:
            _require_identity("reference_identity", self.reference_identity)
        if self.scale is not None and (type(self.scale) is not int or self.scale < 0):
            raise ValueError("scale must be a non-negative integer")
        if self.kind is BarMutationKind.REPAIRED and any(
            value is None
            for value in (self.factor, self.before, self.after, self.reference_identity, self.scale)
        ):
            raise ValueError(
                "REPAIRED mutations require factor, before, after, reference_identity, and scale"
            )
        if self.kind is BarMutationKind.DROPPED:
            if self.before is None or self.after is not None:
                raise ValueError("DROPPED mutations require before and forbid after")


@dataclass(frozen=True, slots=True)
class QualityReport:
    quality: QualityStatus
    completeness: CompletenessStatus
    mutations: tuple[BarMutation, ...] = ()
    messages: tuple[str, ...] = ()
    missing_trade_days: tuple[date, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.quality, QualityStatus):
            raise TypeError("quality must be QualityStatus")
        if not isinstance(self.completeness, CompletenessStatus):
            raise TypeError("completeness must be CompletenessStatus")
        if not isinstance(self.mutations, tuple):
            raise TypeError("mutations must be a tuple")
        if not all(isinstance(mutation, BarMutation) for mutation in self.mutations):
            raise TypeError("mutations must contain BarMutation values")
        if not isinstance(self.messages, tuple):
            raise TypeError("messages must be a tuple")
        if not all(isinstance(message, str) and message.strip() for message in self.messages):
            raise ValueError("messages must contain non-empty strings")
        if not isinstance(self.missing_trade_days, tuple):
            raise TypeError("missing_trade_days must be a tuple")
        if not all(isinstance(day, date) for day in self.missing_trade_days):
            raise TypeError("missing_trade_days must contain date values")
        if self.missing_trade_days != tuple(sorted(set(self.missing_trade_days))):
            raise ValueError("missing_trade_days must be strictly increasing without duplicates")


@dataclass(frozen=True, slots=True)
class QualityAssessment:
    bars: tuple[Bar, ...]
    report: QualityReport

    def __post_init__(self) -> None:
        if not isinstance(self.bars, tuple) or not all(isinstance(bar, Bar) for bar in self.bars):
            raise TypeError("bars must be a tuple of Bar values")
        if not isinstance(self.report, QualityReport):
            raise TypeError("report must be a QualityReport")


def _identity_key(bar: Bar) -> tuple[str, str, datetime, str]:
    return (str(bar.symbol), str(bar.timeframe), bar.open_time, str(bar.adjustment))


def _snapshot(bar: Bar) -> BarValueSnapshot:
    return BarValueSnapshot(
        bar.open, bar.high, bar.low, bar.close, bar.volume, bar.amount, bar.pre_close
    )


def _canonicalize(bars: tuple[Bar, ...]) -> tuple[tuple[Bar, ...], bool, bool, bool]:
    ordered = tuple(sorted(bars, key=_identity_key))
    reordered = ordered != bars
    unique: list[Bar] = []
    collapsed = False
    for bar in ordered:
        if unique and bar.identity == unique[-1].identity:
            if bar != unique[-1]:
                return (), reordered, False, True
            collapsed = True
            continue
        unique.append(bar)
    return tuple(unique), reordered, collapsed, False


def _validated_targets(range_: DateRange, bars: tuple[Bar, ...]) -> None:
    if not bars:
        return
    first = bars[0]
    for bar in bars:
        if bar.symbol != first.symbol or bar.adjustment != first.adjustment:
            raise ValueError("targets must have one symbol and adjustment")
        if bar.timeframe is not Timeframe.DAY_1:
            raise ValueError("targets must be daily bars")
        if not range_.contains(bar.open_time):
            raise ValueError("target open_time must be inside range")


def _validated_reference_input(
    bars: tuple[Bar, ...], target: Bar | None, *, adjustment: Adjustment | None
) -> None:
    for bar in bars:
        if bar.timeframe is not Timeframe.DAY_1:
            raise ValueError("reference bars must be daily")
        if target is not None and bar.symbol != target.symbol:
            raise ValueError("reference bars must match target symbol")
        if adjustment is not None and bar.adjustment is not adjustment:
            raise ValueError("reference bars have an invalid adjustment")


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    repair_scale: int = 4

    def __post_init__(self) -> None:
        if type(self.repair_scale) is not int or not 0 <= self.repair_scale <= 8:
            raise ValueError("repair_scale must be an integer from 0 to 8")

    def assess(
        self,
        *,
        range: DateRange,
        bars: tuple[Bar, ...],
        same_adjustment_daily_references: tuple[Bar, ...],
        none_daily_factor_bars: tuple[Bar, ...],
        calendar_trade_days: tuple[date, ...] | None,
    ) -> QualityAssessment:
        if not isinstance(range, DateRange):
            raise TypeError("range must be DateRange")
        for name, value in (
            ("bars", bars),
            ("same_adjustment_daily_references", same_adjustment_daily_references),
            ("none_daily_factor_bars", none_daily_factor_bars),
        ):
            if not isinstance(value, tuple) or not all(isinstance(item, Bar) for item in value):
                raise TypeError(f"{name} must be a tuple of Bar values")
        _validated_targets(range, bars)
        target = bars[0] if bars else None
        _validated_reference_input(
            same_adjustment_daily_references,
            target,
            adjustment=target.adjustment if target else None,
        )
        _validated_reference_input(none_daily_factor_bars, target, adjustment=Adjustment.NONE)
        if calendar_trade_days is not None:
            if not isinstance(calendar_trade_days, tuple) or not all(
                isinstance(day, date) for day in calendar_trade_days
            ):
                raise TypeError("calendar_trade_days must be a tuple of date values")
            if calendar_trade_days != tuple(sorted(set(calendar_trade_days))):
                raise ValueError(
                    "calendar_trade_days must be strictly increasing without duplicates"
                )
            for day in calendar_trade_days:
                session_open = datetime.combine(day, time(9, 30), SHANGHAI)
                if not range.contains(session_open):
                    raise ValueError("calendar trade day session must be inside range")

        targets, target_reordered, target_collapsed, target_conflict = _canonicalize(bars)
        references, reference_reordered, reference_collapsed, reference_conflict = _canonicalize(
            same_adjustment_daily_references
        )
        factors, factor_reordered, factor_collapsed, factor_conflict = _canonicalize(
            none_daily_factor_bars
        )
        if target_conflict or reference_conflict or factor_conflict:
            return self._rejected()

        messages: list[str] = []
        degraded = target_reordered or reference_reordered or factor_reordered
        if target_reordered or reference_reordered or factor_reordered:
            messages.append("INPUT_REORDERED")
        if target_collapsed or reference_collapsed or factor_collapsed:
            degraded = True
            messages.append("EXACT_DUPLICATE_COLLAPSED")
        reference_by_day = {bar.trading_date: bar for bar in references}
        factor_by_day = {bar.trading_date: bar for bar in factors}
        qualified: list[Bar] = []
        mutations: list[BarMutation] = []
        any_drop = False
        calendar_set = set(calendar_trade_days) if calendar_trade_days is not None else set()
        for current in targets:
            reference = reference_by_day.get(current.trading_date)
            if reference is None:
                degraded = True
                messages.append("MISSING_SAME_ADJUSTMENT_REFERENCE")
                qualified.append(current)
                continue
            if current.adjustment is Adjustment.NONE:
                if current != reference:
                    any_drop = True
                    mutations.append(
                        BarMutation(
                            BarMutationKind.DROPPED,
                            current.identity,
                            "NONE_ADJUSTMENT_REFERENCE_MISMATCH",
                            before=_snapshot(current),
                            reference_identity=reference.identity,
                        )
                    )
                else:
                    qualified.append(current)
                continue
            if current == reference:
                qualified.append(current)
                continue
            if calendar_trade_days is None or current.trading_date not in calendar_set:
                degraded = True
                messages.append("INSUFFICIENT_REPAIR_EVIDENCE")
                qualified.append(current)
                continue
            calendar_index = calendar_trade_days.index(current.trading_date)
            if calendar_index + 1 >= len(calendar_trade_days):
                degraded = True
                messages.append("INSUFFICIENT_REPAIR_EVIDENCE")
                qualified.append(current)
                continue
            factor = factor_by_day.get(current.trading_date)
            next_factor = factor_by_day.get(calendar_trade_days[calendar_index + 1])
            if factor is None or next_factor is None:
                degraded = True
                messages.append("INSUFFICIENT_REPAIR_EVIDENCE")
                qualified.append(current)
                continue
            if factor.close <= 0 or next_factor.pre_close is None:
                any_drop = True
                mutations.append(
                    BarMutation(
                        BarMutationKind.DROPPED,
                        current.identity,
                        "INVALID_REPAIR_EVIDENCE",
                        before=_snapshot(current),
                        reference_identity=reference.identity,
                    )
                )
                continue
            context = Context(prec=28, rounding=ROUND_HALF_UP)
            repair_factor = context.divide(next_factor.pre_close, factor.close)
            quantum = Decimal(1).scaleb(-self.repair_scale)

            def repaired(value: Decimal) -> Decimal:
                return (value * repair_factor).quantize(quantum, rounding=ROUND_HALF_UP)

            candidate = replace(
                current,
                open=repaired(current.open),
                high=repaired(current.high),
                low=repaired(current.low),
                close=repaired(current.close),
                pre_close=repaired(current.pre_close) if current.pre_close is not None else None,
            )
            if (
                candidate.open,
                candidate.high,
                candidate.low,
                candidate.close,
                candidate.pre_close,
            ) != (
                reference.open,
                reference.high,
                reference.low,
                reference.close,
                reference.pre_close,
            ):
                any_drop = True
                mutations.append(
                    BarMutation(
                        BarMutationKind.DROPPED,
                        current.identity,
                        "UNREPAIRABLE_ADJUSTMENT_DISCONTINUITY",
                        before=_snapshot(current),
                        reference_identity=reference.identity,
                    )
                )
                continue
            mutations.append(
                BarMutation(
                    BarMutationKind.REPAIRED,
                    current.identity,
                    "ADJUSTMENT_DISCONTINUITY_REPAIRED",
                    repair_factor,
                    _snapshot(current),
                    _snapshot(candidate),
                    reference.identity,
                    self.repair_scale,
                )
            )
            qualified.append(candidate)

        missing: tuple[date, ...] = ()
        if calendar_trade_days is None:
            completeness = CompletenessStatus.UNKNOWN
            degraded = True
        else:
            observed = {bar.trading_date for bar in qualified}
            missing = tuple(day for day in calendar_trade_days if day not in observed)
            completeness = (
                CompletenessStatus.COMPLETE if not missing else CompletenessStatus.INCOMPLETE
            )
        quality = QualityStatus.REJECTED if any_drop and not qualified else QualityStatus.DEGRADED
        if quality is not QualityStatus.REJECTED:
            quality = QualityStatus.DEGRADED if degraded or any_drop else QualityStatus.VALIDATED
        report = QualityReport(
            quality,
            completeness,
            tuple(mutations),
            tuple(dict.fromkeys(messages)),
            missing,
        )
        return QualityAssessment(tuple(qualified), report)

    @staticmethod
    def _rejected() -> QualityAssessment:
        return QualityAssessment(
            (), QualityReport(QualityStatus.REJECTED, CompletenessStatus.UNKNOWN)
        )
