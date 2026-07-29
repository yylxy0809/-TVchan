"""Stable, transport-independent market data failures."""

from __future__ import annotations

from enum import StrEnum


def _require_safe_message(message: str) -> None:
    forbidden = ("://", "@", "credential", "password", "secret", "token")
    if (
        not isinstance(message, str)
        or not message.strip()
        or any(part in message.lower() for part in forbidden)
    ):
        raise ValueError("message must be safe non-empty text without credentials or a URL")


class MarketDataErrorCode(StrEnum):
    INVALID_QUERY = "INVALID_QUERY"
    UNSUPPORTED_TIMEFRAME = "UNSUPPORTED_TIMEFRAME"
    SYMBOL_NOT_FOUND = "SYMBOL_NOT_FOUND"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_PROTOCOL_ERROR = "PROVIDER_PROTOCOL_ERROR"
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR"
    DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"

    @property
    def retryable(self) -> bool:
        return self in {
            MarketDataErrorCode.PROVIDER_UNAVAILABLE,
            MarketDataErrorCode.PROVIDER_TIMEOUT,
        }


class MarketDataError(Exception):
    """A stable failure with a safe message for callers and logs."""

    def __init__(self, code: MarketDataErrorCode, message: str) -> None:
        if not isinstance(code, MarketDataErrorCode):
            raise TypeError("code must be MarketDataErrorCode")
        _require_safe_message(message)
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

    @property
    def retryable(self) -> bool:
        return self.code.retryable
