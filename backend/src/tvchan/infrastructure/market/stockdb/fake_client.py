"""Traceable fake StockDB public client backed by fixtures (no live service)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

FaultKind = Literal[
    "none",
    "unavailable",
    "timeout",
    "protocol_error",
    "malformed_row",
    "symbol_missing",
]


class FakeStockDBPublicClient:
    """Implements only the public get_data read surface.

    Write methods exist solely so tests can prove the adapter never calls them.
    """

    def __init__(
        self,
        fixture_path: Path | str,
        *,
        fault: FaultKind = "none",
        known_codes: set[str] | None = None,
    ) -> None:
        self.fixture_path = Path(fixture_path)
        self.fault: FaultKind = fault
        self.known_codes = known_codes
        self.calls: list[dict[str, Any]] = []
        self.write_calls: list[str] = []
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or "bars" not in payload:
            raise ValueError("fixture must be an object with a bars map")
        self._bars: dict[str, dict[str, list[dict[str, Any]]]] = payload["bars"]
        self._securities: dict[str, dict[str, Any]] = payload.get("securities", {})
        self.fixture_id: str = str(payload.get("fixture_id", self.fixture_path.name))
        self.fixture_sha256_note: str = str(payload.get("note", ""))

    # ---- public surface ----------------------------------------------------

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
    ) -> Any:
        if as_df:
            raise RuntimeError("as_df is not supported by the fake client")
        if isinstance(code, list):
            return {
                item: self.get_data(item, start, end, frequency, fields, limit, desc, False, fq)
                for item in code
            }

        self.calls.append(
            {
                "code": code,
                "start": start,
                "end": end,
                "frequency": frequency,
                "fields": fields,
                "limit": limit,
                "desc": desc,
                "fq": fq,
            }
        )
        if self.fault == "unavailable":
            raise ConnectionError("connection refused by fixture fault")
        if self.fault == "timeout":
            raise TimeoutError("fixture induced timeout")
        if self.fault == "protocol_error":
            raise RuntimeError("fixture induced protocol failure")
        if self.fault == "symbol_missing":
            return []
        if self.known_codes is not None and code not in self.known_codes:
            return []

        by_freq = self._bars.get(code, {})
        rows = deepcopy(by_freq.get(frequency, []))
        # Apply public fq label only as a provenance tag in fixtures; values already
        # encode the requested adjustment set in the fixture file.
        if fq in {"qfq", "hfq"}:
            tag = fq
            rows = [self._tag_adjustment(row, tag) for row in rows]
        rows = self._filter_range(rows, start=start, end=end, frequency=frequency)
        if desc:
            rows = list(reversed(rows))
        if limit is not None:
            rows = rows[:limit]
        if self.fault == "malformed_row" and rows:
            rows = [{"date": "not-a-date", "open": "x"}]
        return rows

    # ---- write surface (must never be called by adapter) -------------------

    def put(self, *args: Any, **kwargs: Any) -> None:
        self.write_calls.append("put")
        raise AssertionError("write API put must not be called")

    def set(self, *args: Any, **kwargs: Any) -> None:
        self.write_calls.append("set")
        raise AssertionError("write API set must not be called")

    def write(self, *args: Any, **kwargs: Any) -> None:
        self.write_calls.append("write")
        raise AssertionError("write API write must not be called")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        self.write_calls.append("delete")
        raise AssertionError("write API delete must not be called")

    def mset(self, *args: Any, **kwargs: Any) -> None:
        self.write_calls.append("mset")
        raise AssertionError("write API mset must not be called")

    # ---- helpers -----------------------------------------------------------

    @staticmethod
    def _tag_adjustment(row: dict[str, Any], tag: str) -> dict[str, Any]:
        out = dict(row)
        out["_fixture_fq"] = tag
        return out

    @staticmethod
    def _filter_range(
        rows: list[dict[str, Any]],
        *,
        start: str | None,
        end: str | None,
        frequency: str,
    ) -> list[dict[str, Any]]:
        def key(row: dict[str, Any]) -> str:
            return str(row.get("date", ""))

        filtered: list[dict[str, Any]] = []
        for row in rows:
            stamp = key(row)
            if start and stamp < start:
                continue
            # Fake mirrors common SDK inclusive end; gateway applies half-open filter.
            if end and stamp > end:
                continue
            filtered.append(row)
        return filtered
