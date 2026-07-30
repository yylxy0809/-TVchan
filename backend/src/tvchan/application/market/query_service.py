"""Minimal offline MarketDataQueryService vertical (Wave 1 application slice)."""

from __future__ import annotations

from dataclasses import dataclass

from tvchan.application.market.query_limits import QueryLimits
from tvchan.application.ports import MarketDataGateway, TradingCalendarPort
from tvchan.domain.market import (
    Adjustment,
    Bar,
    BarProvenance,
    BarQuery,
    CompletenessStatus,
    MarketDataError,
    MarketDataErrorCode,
    QualityAssessment,
    QualityPolicy,
    QualityReport,
    QualityStatus,
    Timeframe,
)


@dataclass(frozen=True, slots=True)
class MarketDataQueryResult:
    """Application query outcome: qualified bars, quality report, retrieval provenance."""

    bars: tuple[Bar, ...]
    report: QualityReport
    retrieval_provenance: BarProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.bars, tuple) or not all(isinstance(bar, Bar) for bar in self.bars):
            raise TypeError("bars must be a tuple of Bar values")
        if not isinstance(self.report, QualityReport):
            raise TypeError("report must be a QualityReport")
        if not isinstance(self.retrieval_provenance, BarProvenance):
            raise TypeError("retrieval_provenance must be a BarProvenance")


class MarketDataQueryService:
    """Historical bar query orchestration over injected ports and domain policy.

    Order:
      1. QueryLimits.enforce (zero I/O on oversize)
      2. MarketDataGateway.get_bars
      3. TradingCalendarPort.list_trade_days (daily quality path)
      4. QualityPolicy.assess with *injected* reference/factor inputs only

    This slice never performs a second provider query for QFQ/HFQ repair references.
    Callers that need repair must inject same_adjustment_daily_references and
    none_daily_factor_bars. Non-daily targets are outside QualityPolicy's daily
    contract: bars pass through with completeness UNKNOWN and quality VALIDATED
    (provider conflicts already surface as typed gateway errors).
    """

    def __init__(
        self,
        gateway: MarketDataGateway,
        calendar: TradingCalendarPort,
        *,
        quality_policy: QualityPolicy | None = None,
        limits: QueryLimits | None = None,
        same_adjustment_daily_references: tuple[Bar, ...] = (),
        none_daily_factor_bars: tuple[Bar, ...] = (),
    ) -> None:
        self._gateway = gateway
        self._calendar = calendar
        self._policy = quality_policy if quality_policy is not None else QualityPolicy()
        self._limits = limits if limits is not None else QueryLimits()
        if not isinstance(same_adjustment_daily_references, tuple) or not all(
            isinstance(bar, Bar) for bar in same_adjustment_daily_references
        ):
            raise TypeError("same_adjustment_daily_references must be a tuple of Bar values")
        if not isinstance(none_daily_factor_bars, tuple) or not all(
            isinstance(bar, Bar) for bar in none_daily_factor_bars
        ):
            raise TypeError("none_daily_factor_bars must be a tuple of Bar values")
        self._same_adjustment_daily_references = same_adjustment_daily_references
        self._none_daily_factor_bars = none_daily_factor_bars

    def query_bars(self, query: BarQuery) -> MarketDataQueryResult:
        self._limits.enforce(query)
        retrieved = self._gateway.get_bars(query)
        assessment = self._assess(query, retrieved.bars)
        return MarketDataQueryResult(
            bars=assessment.bars,
            report=assessment.report,
            retrieval_provenance=retrieved.provenance,
        )

    def _assess(self, query: BarQuery, bars: tuple[Bar, ...]) -> QualityAssessment:
        if query.timeframe is not Timeframe.DAY_1:
            # QualityPolicy contract is daily-target only; do not invent repair I/O.
            return QualityAssessment(
                bars,
                QualityReport(
                    QualityStatus.VALIDATED,
                    CompletenessStatus.UNKNOWN,
                    messages=("NON_DAILY_QUALITY_PASSTHROUGH",),
                ),
            )
        try:
            trade_days = self._calendar.list_trade_days(query.range)
        except Exception as exc:  # noqa: BLE001 - calendar is a port boundary
            raise MarketDataError(
                MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR,
                "trading calendar failed for the requested range",
            ) from exc
        # Injected references/factors only — no implicit second gateway call.
        return self._policy.assess(
            range=query.range,
            bars=bars,
            same_adjustment_daily_references=self._filter_injected_daily(
                self._same_adjustment_daily_references,
                query,
                expected_adjustment=query.adjustment,
            ),
            none_daily_factor_bars=self._filter_injected_daily(
                self._none_daily_factor_bars,
                query,
                expected_adjustment=Adjustment.NONE,
            ),
            calendar_trade_days=trade_days,
        )

    @staticmethod
    def _filter_injected_daily(
        bars: tuple[Bar, ...],
        query: BarQuery,
        *,
        expected_adjustment: Adjustment,
    ) -> tuple[Bar, ...]:
        """Select injected daily bars that match the query symbol/adjustment.

        Does not call any provider. Bars outside the query range are left for
        QualityPolicy validation (session must be inside range when used as calendar).
        """
        return tuple(
            bar
            for bar in bars
            if bar.symbol == query.symbol
            and bar.timeframe is Timeframe.DAY_1
            and bar.adjustment is expected_adjustment
        )
