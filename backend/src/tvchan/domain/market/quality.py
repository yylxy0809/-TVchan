"""Immutable quality and completeness result vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from tvchan.domain.market.model import Adjustment, BarIdentity, Symbol, Timeframe


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
