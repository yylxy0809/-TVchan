"""Shared fixtures for StockDB adapter offline tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from tvchan.domain.market import Adjustment, BarQuery, DateRange, Symbol, Timeframe
from tvchan.infrastructure.market.stockdb import (
    FakeStockDBPublicClient,
    StockDBReadOnlyGateway,
    StockDBSettings,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "stockdb"
BARS_FIXTURE = FIXTURES / "bars_600000.json"


@pytest.fixture
def fixture_path() -> Path:
    return BARS_FIXTURE


@pytest.fixture
def settings() -> StockDBSettings:
    return StockDBSettings(
        host="127.0.0.1",
        port=7899,
        timeout_ms=1000,
        provider_name="stockdb-sdk-fixture",
        allow_live=False,
    )


@pytest.fixture
def fixed_clock() -> datetime:
    return datetime(2026, 1, 8, 2, 0, 0, tzinfo=UTC)


@pytest.fixture
def fake_client(fixture_path: Path) -> FakeStockDBPublicClient:
    return FakeStockDBPublicClient(
        fixture_path,
        known_codes={"600000", "000001"},
    )


@pytest.fixture
def gateway(
    settings: StockDBSettings,
    fake_client: FakeStockDBPublicClient,
    fixed_clock: datetime,
) -> StockDBReadOnlyGateway:
    return StockDBReadOnlyGateway(
        settings,
        client=fake_client,
        known_symbols=frozenset({"600000", "000001"}),
        clock=lambda: fixed_clock,
    )


@pytest.fixture
def daily_query() -> BarQuery:
    return BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),  # 09:30 Asia/Shanghai
            datetime(2026, 1, 7, 1, 30, tzinfo=UTC),  # exclusive end -> 2026-01-07 not included
        ),
        limit=100,
        adjustment=Adjustment.NONE,
    )
