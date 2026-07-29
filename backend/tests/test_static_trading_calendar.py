from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from tvchan.domain.market import DateRange
from tvchan.infrastructure.market.static_trading_calendar import (
    StaticTradingCalendarAdapter,
    StaticTradingCalendarSnapshot,
)


def _snapshot() -> StaticTradingCalendarSnapshot:
    return StaticTradingCalendarSnapshot(
        "2026-01-01", "Asia/Shanghai", (date(2026, 1, 2), date(2026, 1, 5))
    )


def test_returns_only_session_opens_inside_the_half_open_range() -> None:
    adapter = StaticTradingCalendarAdapter((_snapshot(),), "2026-01-01")
    interval = DateRange(
        datetime(2026, 1, 2, 1, 30, tzinfo=UTC),
        datetime(2026, 1, 5, 1, 30, tzinfo=UTC),
    )

    assert adapter.list_trade_days(interval) == (date(2026, 1, 2),)


def test_snapshot_and_adapter_are_versioned_and_immutable() -> None:
    snapshot = _snapshot()
    adapter = StaticTradingCalendarAdapter((snapshot,), "2026-01-01")

    assert adapter.snapshots == (snapshot,)
    with pytest.raises(ValueError, match="unknown calendar version"):
        StaticTradingCalendarAdapter((snapshot,), "2026-01-02")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: StaticTradingCalendarSnapshot("2026-1-1", "Asia/Shanghai", ()),
        lambda: StaticTradingCalendarSnapshot("2026-01-01", "UTC", ()),
        lambda: StaticTradingCalendarSnapshot(
            "2026-01-01", "Asia/Shanghai", (date(2026, 1, 5), date(2026, 1, 2))
        ),
    ],
)
def test_snapshot_rejects_invalid_contract_values(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]


def test_adapter_rejects_duplicate_snapshot_versions() -> None:
    with pytest.raises(ValueError, match="unique"):
        StaticTradingCalendarAdapter((_snapshot(), _snapshot()), "2026-01-01")
