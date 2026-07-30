"""Narrow public surface the adapter is allowed to call on a StockDB client."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StockDBPublicClient(Protocol):
    """Only the public get_data read surface.

    Implementations must not expose write APIs used by the adapter.
    Private helpers (_apply_fq_in_memory, _merge_*, etc.) are intentionally absent.
    """

    def get_data(
        self,
        code: str | list[str],
        start: str | None = None,
        end: str | None = None,
        frequency: str = "1d",
        fields: str | list[str] | None = None,
        limit: int | None = None,
        desc: bool = False,
        as_df: bool = False,
        fq: str | None = "qfq",
    ) -> Any: ...
