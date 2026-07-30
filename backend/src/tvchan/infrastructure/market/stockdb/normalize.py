"""Normalize public StockDB row dicts into canonical Bar values."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from tvchan.domain.market import (
    Adjustment,
    Bar,
    BarProvenance,
    MarketDataError,
    MarketDataErrorCode,
    Symbol,
    Timeframe,
)
from tvchan.domain.market.model import SHANGHAI

_OPENING = time(9, 30)
_DAILY_LIKE = frozenset({Timeframe.DAY_1, Timeframe.WEEK_1, Timeframe.MONTH_1})


def decimal_from_raw(name: str, value: Any, *, positive: bool) -> Decimal | None:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal):
            result = value
        elif isinstance(value, (int, str)):
            result = Decimal(str(value))
        elif isinstance(value, float):
            # Public SDK may return float; convert via str to avoid binary artifacts
            # being silently accepted as exact. This is an adapter boundary conversion.
            result = Decimal(str(value))
        else:
            raise MarketDataError(
                MarketDataErrorCode.NORMALIZATION_ERROR,
                f"field {name} has unsupported type",
            )
    except (InvalidOperation, ValueError) as exc:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            f"field {name} is not a finite decimal",
        ) from exc
    if not result.is_finite():
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            f"field {name} is not a finite decimal",
        )
    if positive and result <= 0:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            f"field {name} must be positive",
        )
    if not positive and result < 0:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            f"field {name} must not be negative",
        )
    return result


def parse_source_open_time(raw: Any, timeframe: Timeframe) -> datetime:
    """Parse StockDB date field into Asia/Shanghai-aware open_time."""
    if raw is None:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            "row missing date field",
        )
    raw_str = str(raw).strip()
    try:
        if len(raw_str) == 8 and raw_str.isdigit():
            # Daily / weekly / monthly provider stamp: period open at 09:30 Asia/Shanghai
            day = datetime.strptime(raw_str, "%Y%m%d").date()
            if timeframe in _DAILY_LIKE:
                return datetime.combine(day, _OPENING, tzinfo=SHANGHAI)
            # Unexpected bare day for minute bar — treat as session open
            return datetime.combine(day, _OPENING, tzinfo=SHANGHAI)
        if len(raw_str) == 14 and raw_str.isdigit():
            dt = datetime.strptime(raw_str, "%Y%m%d%H%M%S").replace(tzinfo=SHANGHAI)
            if timeframe in _DAILY_LIKE:
                # Daily-like stamped as datetime: normalize to 09:30 on that calendar day
                return datetime.combine(dt.date(), _OPENING, tzinfo=SHANGHAI)
            return dt
    except ValueError as exc:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            "row date is malformed",
        ) from exc
    raise MarketDataError(
        MarketDataErrorCode.NORMALIZATION_ERROR,
        "row date has unsupported format",
    )


def row_to_bar(
    *,
    row: dict[str, Any],
    symbol: Symbol,
    timeframe: Timeframe,
    adjustment: Adjustment,
    provider: str,
    retrieved_at: datetime,
    source_identity: str,
) -> Bar:
    if not isinstance(row, dict):
        raise MarketDataError(
            MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR,
            "provider returned a non-object row",
        )
    open_time = parse_source_open_time(row.get("date"), timeframe)
    trading_date: date = open_time.astimezone(SHANGHAI).date()
    open_ = decimal_from_raw("open", row.get("open"), positive=True)
    high = decimal_from_raw("high", row.get("high"), positive=True)
    low = decimal_from_raw("low", row.get("low"), positive=True)
    close = decimal_from_raw("close", row.get("close"), positive=True)
    if open_ is None or high is None or low is None or close is None:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            "row missing required OHLC fields",
        )
    volume = decimal_from_raw("volume", row.get("volume"), positive=False)
    amount = decimal_from_raw("amount", row.get("amount"), positive=False)
    pre_close_raw = row.get("pre_close")
    pre_close: Decimal | None
    if timeframe is Timeframe.DAY_1:
        pre_close = decimal_from_raw("pre_close", pre_close_raw, positive=True)
    else:
        # pre_close only defined for daily bars in the canonical model
        pre_close = None

    transformations: list[str] = ["public_get_data", f"adjustment={adjustment.value}"]
    if adjustment is not Adjustment.NONE:
        transformations.append("sdk_public_fq_parameter")

    provenance = BarProvenance(
        provider=provider,
        source_time=retrieved_at,
        source_identity=source_identity,
        transformations=tuple(transformations),
    )
    try:
        return Bar(
            symbol=symbol,
            timeframe=timeframe,
            open_time=open_time,
            trading_date=trading_date,
            adjustment=adjustment,
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            amount=amount,
            pre_close=pre_close,
            provenance=provenance,
        )
    except (TypeError, ValueError) as exc:
        raise MarketDataError(
            MarketDataErrorCode.NORMALIZATION_ERROR,
            "row failed canonical bar validation",
        ) from exc
