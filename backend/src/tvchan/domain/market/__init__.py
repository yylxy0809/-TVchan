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
    BarValueSnapshot,
    CompletenessStatus,
    QualityAssessment,
    QualityPolicy,
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
    "BarValueSnapshot",
    "CompletenessStatus",
    "DateRange",
    "DependencyHealth",
    "DependencyStatus",
    "Exchange",
    "MarketDataError",
    "MarketDataErrorCode",
    "QualityAssessment",
    "QualityPolicy",
    "QualityReport",
    "QualityStatus",
    "RetrievedBars",
    "Security",
    "Symbol",
    "Timeframe",
]
