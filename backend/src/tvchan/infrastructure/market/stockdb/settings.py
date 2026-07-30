"""Typed StockDB adapter settings (bootstrap-injected; no env scrape inside adapter)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StockDBSettings:
    host: str = "127.0.0.1"
    port: int = 7899
    # Password is intentionally not stored here for prototype safety; inject via client factory.
    timeout_ms: int = 5_000
    provider_name: str = "stockdb-sdk"
    # When True, live SDK import is attempted; otherwise only injected client is used.
    allow_live: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("host must be non-empty")
        if (
            isinstance(self.port, bool)
            or not isinstance(self.port, int)
            or not (1 <= self.port <= 65535)
        ):
            raise ValueError("port must be 1..65535")
        if (
            isinstance(self.timeout_ms, bool)
            or not isinstance(self.timeout_ms, int)
            or self.timeout_ms <= 0
        ):
            raise ValueError("timeout_ms must be a positive integer")
        if not isinstance(self.provider_name, str) or not self.provider_name.strip():
            raise ValueError("provider_name must be non-empty")
        forbidden = ("://", "@", "password", "secret", "token")
        if any(part in self.provider_name.lower() for part in forbidden):
            raise ValueError("provider_name must not embed credentials")
