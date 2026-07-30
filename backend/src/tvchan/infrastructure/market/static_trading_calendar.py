"""Versioned in-memory trading calendars with no provider dependency."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from tvchan.domain.market import DateRange
from tvchan.domain.market.model import SHANGHAI


def _require_version(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be an ISO YYYY-MM-DD version")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO YYYY-MM-DD version") from error
    if value != parsed.isoformat():
        raise ValueError(f"{name} must be an ISO YYYY-MM-DD version")
    return value


def _require_trade_days(value: object) -> tuple[date, ...]:
    if not isinstance(value, tuple):
        raise TypeError("trade_days must be a tuple")
    if not all(type(day) is date for day in value):
        raise TypeError("trade_days must contain date values")
    if value != tuple(sorted(value)) or len(value) != len(set(value)):
        raise ValueError("trade_days must be strictly increasing without duplicates")
    return value


@dataclass(frozen=True, slots=True)
class StaticTradingCalendarSnapshot:
    version: str
    timezone: str
    trade_days: tuple[date, ...]

    def __post_init__(self) -> None:
        _require_version(self.version, "version")
        if self.timezone != "Asia/Shanghai":
            raise ValueError("timezone must be Asia/Shanghai")
        _require_trade_days(self.trade_days)


@dataclass(frozen=True, slots=True)
class StaticTradingCalendarAdapter:
    snapshots: tuple[StaticTradingCalendarSnapshot, ...]
    version: str

    def __post_init__(self) -> None:
        if not isinstance(self.snapshots, tuple):
            raise TypeError("snapshots must be a tuple")
        if not all(
            isinstance(snapshot, StaticTradingCalendarSnapshot) for snapshot in self.snapshots
        ):
            raise TypeError("snapshots must contain StaticTradingCalendarSnapshot values")
        _require_version(self.version, "version")
        versions = tuple(snapshot.version for snapshot in self.snapshots)
        if len(versions) != len(set(versions)):
            raise ValueError("snapshot versions must be unique")
        if self.version not in versions:
            raise ValueError("unknown calendar version")

    def list_trade_days(self, range: DateRange) -> tuple[date, ...]:
        if not isinstance(range, DateRange):
            raise TypeError("range must be DateRange")
        snapshot = next(snapshot for snapshot in self.snapshots if snapshot.version == self.version)
        return tuple(
            day
            for day in snapshot.trade_days
            if range.start <= datetime.combine(day, time(9, 30), SHANGHAI) < range.end
        )
