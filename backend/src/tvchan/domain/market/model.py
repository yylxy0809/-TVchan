"""Provider-neutral market facts for the Wave 1 contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias

SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
_OPENING_TIME = time(9, 30)


class Exchange(StrEnum):
    """Canonical A-share exchanges."""

    SSE = "SSE"
    SZSE = "SZSE"


@dataclass(frozen=True, slots=True)
class Symbol:
    """A canonical A-share symbol, never a provider-specific code."""

    value: str

    def __post_init__(self) -> None:
        prefix, separator, code = self.value.partition(":")
        if (
            separator != ":"
            or prefix not in {exchange.value for exchange in Exchange}
            or len(code) != 6
            or not code.isdigit()
        ):
            raise ValueError("symbol must be SSE:<six digits> or SZSE:<six digits>")

    @property
    def exchange(self) -> Exchange:
        return Exchange(self.value[: self.value.index(":")])

    @property
    def code(self) -> str:
        return self.value[self.value.index(":") + 1 :]

    def __str__(self) -> str:
        return self.value


class Timeframe(StrEnum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    MINUTE_60 = "60m"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1mo"


class Adjustment(StrEnum):
    NONE = "NONE"
    QFQ = "QFQ"
    HFQ = "HFQ"


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


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
        raise ValueError(f"{name} must not be negative")


def _require_safe_text(name: str, value: str) -> None:
    forbidden = ("://", "@", "credential", "password", "secret", "token")
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(part in value.lower() for part in forbidden)
    ):
        raise ValueError(f"{name} must be safe text without credentials or a URL")


def _require_instance(name: str, value: object, expected_type: type[object]) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} must be {expected_type.__name__}")


def _require_tuple(name: str, value: object, element_type: type[object]) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be a tuple")
    if not all(isinstance(item, element_type) for item in value):
        raise TypeError(f"{name} must contain {element_type.__name__} values")


@dataclass(frozen=True, slots=True)
class DateRange:
    """A timezone-aware half-open interval, ``[start, end)``."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _require_instance("start", self.start, datetime)
        _require_instance("end", self.end, datetime)
        if not _is_aware(self.start) or not _is_aware(self.end):
            raise ValueError("DateRange boundaries must be timezone-aware")
        if self.start >= self.end:
            raise ValueError("DateRange requires start < end")

    def contains(self, instant: datetime) -> bool:
        if not _is_aware(instant):
            raise ValueError("instant must be timezone-aware")
        return self.start <= instant < self.end


@dataclass(frozen=True, slots=True)
class BarQuery:
    symbol: Symbol
    timeframe: Timeframe
    range: DateRange
    limit: int
    adjustment: Adjustment = Adjustment.NONE

    def __post_init__(self) -> None:
        _require_instance("symbol", self.symbol, Symbol)
        _require_instance("timeframe", self.timeframe, Timeframe)
        _require_instance("range", self.range, DateRange)
        _require_instance("adjustment", self.adjustment, Adjustment)
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit <= 0:
            raise ValueError("limit must be a positive integer")


@dataclass(frozen=True, slots=True)
class BarProvenance:
    provider: str
    source_time: datetime
    source_identity: str
    transformations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_safe_text("provider", self.provider)
        _require_safe_text("source_identity", self.source_identity)
        _require_instance("source_time", self.source_time, datetime)
        if not _is_aware(self.source_time):
            raise ValueError("source_time must be timezone-aware")
        _require_tuple("transformations", self.transformations, str)
        if not all(item.strip() for item in self.transformations):
            raise ValueError("transformations must contain non-empty strings")


BarIdentity: TypeAlias = tuple[Symbol, Timeframe, datetime, Adjustment]


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: Symbol
    timeframe: Timeframe
    open_time: datetime
    trading_date: date
    adjustment: Adjustment
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    amount: Decimal | None
    pre_close: Decimal | None
    provenance: BarProvenance

    def __post_init__(self) -> None:
        _require_instance("symbol", self.symbol, Symbol)
        _require_instance("timeframe", self.timeframe, Timeframe)
        _require_instance("open_time", self.open_time, datetime)
        _require_instance("trading_date", self.trading_date, date)
        _require_instance("adjustment", self.adjustment, Adjustment)
        _require_instance("provenance", self.provenance, BarProvenance)
        if not _is_aware(self.open_time):
            raise ValueError("open_time must be timezone-aware")
        if self.open_time.astimezone(SHANGHAI).date() != self.trading_date:
            raise ValueError("trading_date must be the Asia/Shanghai open date")
        if self.timeframe in {Timeframe.DAY_1, Timeframe.WEEK_1, Timeframe.MONTH_1}:
            if self.open_time.astimezone(SHANGHAI).time() != _OPENING_TIME:
                raise ValueError("daily and higher bars must open at 09:30 Asia/Shanghai")
        for price_name, price in (
            ("open", self.open),
            ("high", self.high),
            ("low", self.low),
            ("close", self.close),
        ):
            _require_decimal(price_name, price, positive=True)
        for quantity_name, quantity in (("volume", self.volume), ("amount", self.amount)):
            _require_decimal(quantity_name, quantity, positive=False)
        _require_decimal("pre_close", self.pre_close, positive=True)
        if self.pre_close is not None and self.timeframe is not Timeframe.DAY_1:
            raise ValueError("pre_close is only defined for daily bars")
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError(
                "OHLC values must satisfy low <= min(open, close) <= max(open, close) <= high"
            )

    @property
    def identity(self) -> BarIdentity:
        return (self.symbol, self.timeframe, self.open_time, self.adjustment)


@dataclass(frozen=True, slots=True)
class Security:
    symbol: Symbol
    name: str | None
    provenance: BarProvenance

    def __post_init__(self) -> None:
        _require_instance("symbol", self.symbol, Symbol)
        _require_instance("provenance", self.provenance, BarProvenance)
        if self.name is not None and (not isinstance(self.name, str) or not self.name.strip()):
            raise ValueError("name must be non-empty when provided")


@dataclass(frozen=True, slots=True)
class RetrievedBars:
    bars: tuple[Bar, ...]
    provenance: BarProvenance

    def __post_init__(self) -> None:
        _require_tuple("bars", self.bars, Bar)
        _require_instance("provenance", self.provenance, BarProvenance)
        keys = tuple(
            (str(bar.symbol), str(bar.timeframe), bar.open_time, str(bar.adjustment))
            for bar in self.bars
        )
        if keys != tuple(sorted(keys)):
            raise ValueError("bars must be sorted by canonical identity")


class DependencyStatus(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True, slots=True)
class DependencyHealth:
    status: DependencyStatus
    provider: str
    checked_at: datetime
    latency_ms: int | None
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_instance("status", self.status, DependencyStatus)
        _require_safe_text("provider", self.provider)
        _require_instance("checked_at", self.checked_at, datetime)
        if not _is_aware(self.checked_at):
            raise ValueError("checked_at must be timezone-aware")
        if self.latency_ms is not None and (
            isinstance(self.latency_ms, bool)
            or not isinstance(self.latency_ms, int)
            or self.latency_ms < 0
        ):
            raise ValueError("latency_ms must be non-negative")
        if self.error_code is not None:
            _require_safe_text("error_code", self.error_code)
