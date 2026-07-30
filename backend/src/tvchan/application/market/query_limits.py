"""Bounded query admission applied before any provider I/O."""

from __future__ import annotations

from dataclasses import dataclass

from tvchan.domain.market import BarQuery, MarketDataError, MarketDataErrorCode


@dataclass(frozen=True, slots=True)
class QueryLimits:
    """Hard caps enforced by the application service before gateway calls."""

    max_limit: int = 5_000

    def __post_init__(self) -> None:
        if (
            type(self.max_limit) is not int
            or isinstance(self.max_limit, bool)
            or self.max_limit <= 0
        ):
            raise ValueError("max_limit must be a positive integer")

    def enforce(self, query: BarQuery) -> None:
        """Reject oversized queries with zero provider I/O.

        Raises MarketDataError(INVALID_QUERY) when the request exceeds caps.
        """
        if not isinstance(query, BarQuery):
            raise MarketDataError(
                MarketDataErrorCode.INVALID_QUERY,
                "query must be a BarQuery",
            )
        if query.limit > self.max_limit:
            raise MarketDataError(
                MarketDataErrorCode.INVALID_QUERY,
                f"query limit exceeds max_limit of {self.max_limit}",
            )
