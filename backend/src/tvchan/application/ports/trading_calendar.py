"""Application boundary for trading-session facts."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from tvchan.domain.market import DateRange


class TradingCalendarPort(Protocol):
    def list_trade_days(self, range: DateRange) -> tuple[date, ...]: ...
