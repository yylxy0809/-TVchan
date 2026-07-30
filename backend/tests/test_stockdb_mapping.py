from __future__ import annotations

from datetime import UTC, datetime

import pytest
from tvchan.domain.market import Adjustment, Symbol, Timeframe
from tvchan.domain.market.model import SHANGHAI
from tvchan.infrastructure.market.stockdb.mapping import (
    ADJUSTMENT_TO_SDK_FQ,
    TIMEFRAME_TO_SDK_FREQUENCY,
    format_sdk_bound,
    map_adjustment_to_sdk,
    map_symbol_to_sdk_code,
    map_timeframe_to_sdk_frequency,
    symbol_from_provider_code,
)


def test_symbol_maps_to_six_digit_code() -> None:
    assert map_symbol_to_sdk_code(Symbol("SSE:600000")) == "600000"
    assert map_symbol_to_sdk_code(Symbol("SZSE:000001")) == "000001"


def test_timeframe_mapping_includes_month_alias() -> None:
    assert map_timeframe_to_sdk_frequency(Timeframe.MONTH_1) == "1M"
    assert TIMEFRAME_TO_SDK_FREQUENCY[Timeframe.DAY_1] == "1d"
    assert TIMEFRAME_TO_SDK_FREQUENCY[Timeframe.MINUTE_30] == "30m"
    assert set(TIMEFRAME_TO_SDK_FREQUENCY) == set(Timeframe)


def test_adjustment_mapping() -> None:
    assert map_adjustment_to_sdk(Adjustment.NONE) is None
    assert map_adjustment_to_sdk(Adjustment.QFQ) == "qfq"
    assert map_adjustment_to_sdk(Adjustment.HFQ) == "hfq"
    assert ADJUSTMENT_TO_SDK_FQ[Adjustment.QFQ] == "qfq"


def test_format_sdk_bound_daily_and_minute() -> None:
    instant = datetime(2026, 1, 2, 1, 30, tzinfo=UTC)  # 09:30 Shanghai
    assert format_sdk_bound(instant, Timeframe.DAY_1) == "20260102"
    assert format_sdk_bound(instant, Timeframe.MINUTE_30) == "20260102093000"
    local = datetime(2026, 1, 2, 9, 30, tzinfo=SHANGHAI)
    assert format_sdk_bound(local, Timeframe.DAY_1) == "20260102"


def test_provider_code_infers_exchange() -> None:
    assert str(symbol_from_provider_code("600000")) == "SSE:600000"
    assert str(symbol_from_provider_code("000001")) == "SZSE:000001"
    with pytest.raises(ValueError):
        symbol_from_provider_code("99999")
