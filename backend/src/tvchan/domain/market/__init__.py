"""Provider-neutral market facts and contracts."""

from tvchan.domain.market.errors import MarketDataError, MarketDataErrorCode
from tvchan.domain.market.model import (
    Adjustment,
    Bar,
    BarIdentity,
    BarProvenance,
    BarQuery,
    DateRange,
    DependencyHealth,
    DependencyStatus,
    Exchange,
    RetrievedBars,
    Security,
    Symbol,
    Timeframe,
)
from tvchan.domain.market.quality import (
    BarMutation,
    BarMutationKind,
    CompletenessStatus,
    QualityReport,
    QualityStatus,
)

__all__ = [
    "Adjustment",
    "Bar",
    "BarIdentity",
    "BarMutation",
    "BarMutationKind",
    "BarProvenance",
    "BarQuery",
    "CompletenessStatus",
    "DateRange",
    "DependencyHealth",
    "DependencyStatus",
    "Exchange",
    "MarketDataError",
    "MarketDataErrorCode",
    "QualityReport",
    "QualityStatus",
    "RetrievedBars",
    "Security",
    "Symbol",
    "Timeframe",
]
