"""Canonical <-> StockDB public SDK mapping (adapter-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Final

from tvchan.domain.market import Adjustment, Exchange, Symbol, Timeframe

# Public SDK frequency strings accepted by StockDBClient.get_data.
TIMEFRAME_TO_SDK_FREQUENCY: Final[dict[Timeframe, str]] = {
    Timeframe.MINUTE_1: "1m",
    Timeframe.MINUTE_5: "5m",
    Timeframe.MINUTE_15: "15m",
    Timeframe.MINUTE_30: "30m",
    Timeframe.MINUTE_60: "60m",
    Timeframe.DAY_1: "1d",
    Timeframe.WEEK_1: "1w",
    Timeframe.MONTH_1: "1M",  # adapter-only: canonical 1mo -> SDK 1M
}

ADJUSTMENT_TO_SDK_FQ: Final[dict[Adjustment, str | None]] = {
    Adjustment.NONE: None,
    Adjustment.QFQ: "qfq",
    Adjustment.HFQ: "hfq",
}


def map_symbol_to_sdk_code(symbol: Symbol) -> str:
    """Map canonical Symbol to StockDB six-digit code (public SDK uses bare code)."""
    return symbol.code


def map_timeframe_to_sdk_frequency(timeframe: Timeframe) -> str:
    try:
        return TIMEFRAME_TO_SDK_FREQUENCY[timeframe]
    except KeyError as exc:  # pragma: no cover - enum is closed
        raise ValueError(f"unsupported timeframe: {timeframe}") from exc


def map_adjustment_to_sdk(adjustment: Adjustment) -> str | None:
    try:
        return ADJUSTMENT_TO_SDK_FQ[adjustment]
    except KeyError as exc:  # pragma: no cover - enum is closed
        raise ValueError(f"unsupported adjustment: {adjustment}") from exc


def format_sdk_bound(instant: datetime, timeframe: Timeframe) -> str:
    """Format a half-open bound for public SDK start/end strings.

    Daily+ uses YYYYMMDD; minute bars use YYYYMMDDHHMMSS in Asia/Shanghai wall time.
    """
    from tvchan.domain.market.model import SHANGHAI

    local = instant.astimezone(SHANGHAI)
    if timeframe in {Timeframe.DAY_1, Timeframe.WEEK_1, Timeframe.MONTH_1}:
        return local.strftime("%Y%m%d")
    return local.strftime("%Y%m%d%H%M%S")


def infer_exchange_from_code(code: str) -> Exchange:
    if code.startswith(("6", "9")):
        return Exchange.SSE
    if code.startswith(("0", "3", "1", "2")):
        return Exchange.SZSE
    raise ValueError(f"cannot infer exchange for code {code}")


def symbol_from_provider_code(code: str) -> Symbol:
    exchange = infer_exchange_from_code(code)
    return Symbol(f"{exchange.value}:{code}")
