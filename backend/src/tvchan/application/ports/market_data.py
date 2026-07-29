"""Application boundary for reading canonical market facts."""

from __future__ import annotations

from typing import Protocol

from tvchan.domain.market import (
    BarQuery,
    DependencyHealth,
    RetrievedBars,
    Security,
    Symbol,
)


class MarketDataGateway(Protocol):
    def get_bars(self, query: BarQuery) -> RetrievedBars: ...

    def get_security(self, symbol: Symbol) -> Security | None: ...

    def probe(self) -> DependencyHealth: ...
