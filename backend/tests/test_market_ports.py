from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

from tvchan.application.ports import MarketDataGateway, TradingCalendarPort
from tvchan.domain.market import (
    Adjustment,
    Bar,
    BarProvenance,
    BarQuery,
    DateRange,
    DependencyHealth,
    DependencyStatus,
    RetrievedBars,
    Security,
    Symbol,
    Timeframe,
)


def test_market_data_gateway_protocol_uses_only_canonical_domain_values() -> None:
    class FakeMarketDataGateway:
        def __init__(
            self, bars: RetrievedBars, security: Security, health: DependencyHealth
        ) -> None:
            self._bars = bars
            self._security = security
            self._health = health

        def get_bars(self, query: BarQuery) -> RetrievedBars:
            return self._bars

        def get_security(self, symbol: Symbol) -> Security | None:
            return self._security if symbol == self._security.symbol else None

        def probe(self) -> DependencyHealth:
            return self._health

    symbol = Symbol("SSE:600000")
    provenance = BarProvenance("fake", datetime(2026, 1, 2, tzinfo=UTC), "fixture")
    bar = Bar(
        symbol,
        Timeframe.DAY_1,
        datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
        date(2026, 1, 2),
        Adjustment.NONE,
        Decimal("10"),
        Decimal("10"),
        Decimal("10"),
        Decimal("10"),
        None,
        None,
        None,
        provenance,
    )
    gateway = cast(
        MarketDataGateway,
        FakeMarketDataGateway(
            RetrievedBars((bar,), provenance),
            Security(symbol, "Fixture", provenance),
            DependencyHealth(DependencyStatus.READY, "fake", datetime(2026, 1, 2, tzinfo=UTC), 0),
        ),
    )
    query = BarQuery(
        symbol,
        Timeframe.DAY_1,
        DateRange(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 3, tzinfo=UTC)),
        10,
    )

    assert gateway.get_bars(query).bars == (bar,)
    assert gateway.get_security(symbol) == Security(symbol, "Fixture", provenance)
    assert gateway.probe().status is DependencyStatus.READY


def test_trading_calendar_port_remains_independent_of_market_gateway() -> None:
    class FakeTradingCalendar:
        def __init__(self, trade_days: tuple[date, ...]) -> None:
            self._trade_days = trade_days

        def list_trade_days(self, range: DateRange) -> tuple[date, ...]:
            return self._trade_days

    calendar = cast(TradingCalendarPort, FakeTradingCalendar((date(2026, 1, 2),)))
    interval = DateRange(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 3, tzinfo=UTC))

    assert calendar.list_trade_days(interval) == (date(2026, 1, 2),)
