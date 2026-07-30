from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from tvchan.domain.market import (
    Adjustment,
    BarQuery,
    DateRange,
    DependencyStatus,
    MarketDataError,
    MarketDataErrorCode,
    Symbol,
    Timeframe,
)
from tvchan.infrastructure.market.stockdb import (
    FakeStockDBPublicClient,
    StockDBReadOnlyGateway,
    StockDBSettings,
)


def _query() -> BarQuery:
    return BarQuery(
        Symbol("SSE:600000"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 7, 1, 30, tzinfo=UTC),
        ),
        limit=10,
        adjustment=Adjustment.NONE,
    )


def test_symbol_not_found(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, known_codes={"600000", "000001"})
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000", "000001"}),
        clock=lambda: fixed_clock,
    )
    query = BarQuery(
        Symbol("SSE:600519"),
        Timeframe.DAY_1,
        DateRange(
            datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
            datetime(2026, 1, 7, 1, 30, tzinfo=UTC),
        ),
        limit=10,
    )
    with pytest.raises(MarketDataError) as exc:
        gateway.get_bars(query)
    assert exc.value.code is MarketDataErrorCode.SYMBOL_NOT_FOUND
    assert not exc.value.retryable


def test_provider_unavailable(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, fault="unavailable")
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000"}),
        clock=lambda: fixed_clock,
    )
    with pytest.raises(MarketDataError) as exc:
        gateway.get_bars(_query())
    assert exc.value.code is MarketDataErrorCode.PROVIDER_UNAVAILABLE
    assert exc.value.retryable


def test_provider_timeout(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, fault="timeout")
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000"}),
        clock=lambda: fixed_clock,
    )
    with pytest.raises(MarketDataError) as exc:
        gateway.get_bars(_query())
    assert exc.value.code is MarketDataErrorCode.PROVIDER_TIMEOUT
    assert exc.value.retryable


def test_malformed_data_normalization_error(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, fault="malformed_row", known_codes={"600000"})
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000"}),
        clock=lambda: fixed_clock,
    )
    with pytest.raises(MarketDataError) as exc:
        gateway.get_bars(_query())
    assert exc.value.code is MarketDataErrorCode.NORMALIZATION_ERROR
    assert not exc.value.retryable


def test_protocol_error(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, fault="protocol_error")
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        known_symbols=frozenset({"600000"}),
        clock=lambda: fixed_clock,
    )
    with pytest.raises(MarketDataError) as exc:
        gateway.get_bars(_query())
    assert exc.value.code is MarketDataErrorCode.PROVIDER_PROTOCOL_ERROR
    assert not exc.value.retryable


def test_probe_not_ready_on_unavailable(
    settings: StockDBSettings, fixture_path: Path, fixed_clock: datetime
) -> None:
    client = FakeStockDBPublicClient(fixture_path, fault="unavailable")
    gateway = StockDBReadOnlyGateway(
        settings,
        client=client,
        clock=lambda: fixed_clock,
    )
    health = gateway.probe()
    assert health.status is DependencyStatus.NOT_READY
    assert health.error_code == MarketDataErrorCode.PROVIDER_UNAVAILABLE.value


def test_probe_ready_on_fixture(gateway: StockDBReadOnlyGateway) -> None:
    health = gateway.probe()
    assert health.status is DependencyStatus.READY
    assert health.error_code is None
    assert health.latency_ms is not None and health.latency_ms >= 0


def test_get_security_none_for_unknown(gateway: StockDBReadOnlyGateway) -> None:
    assert gateway.get_security(Symbol("SSE:600519")) is None


def test_get_security_for_known(gateway: StockDBReadOnlyGateway) -> None:
    security = gateway.get_security(Symbol("SSE:600000"))
    assert security is not None
    assert security.symbol == Symbol("SSE:600000")
    assert security.name == "SPDB"


def test_live_disabled_without_client_raises_unavailable() -> None:
    settings = StockDBSettings(allow_live=False)
    gateway = StockDBReadOnlyGateway(settings)
    with pytest.raises(MarketDataError) as exc:
        gateway.get_bars(_query())
    assert exc.value.code is MarketDataErrorCode.PROVIDER_UNAVAILABLE
