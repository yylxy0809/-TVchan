"""Offline-only live-capability contract tests (formal C002).

Frozen fixtures/stockdb/live_capability.json is the formal live conclusion.
This module never enables live mode, never probes a live provider, and never
writes live_capability artifacts.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "stockdb"
LIVE_STATUS_PATH = FIXTURES / "live_capability.json"
TESTS = Path(__file__).resolve().parent
STOCKDB_TEST_PREFIX = "test_stockdb_"


def test_frozen_live_capability_is_not_verified() -> None:
    """Formal live conclusion is a frozen artifact, not a pytest side effect."""
    assert LIVE_STATUS_PATH.is_file(), "live_capability.json must be frozen into fixtures"
    payload = json.loads(LIVE_STATUS_PATH.read_text(encoding="utf-8"))
    assert payload["capability"] == "stockdb_public_sdk_live_get_data"
    assert payload["status"] == "NOT_VERIFIED"
    assert payload.get("reason"), "NOT_VERIFIED requires an explicit reason"
    assert payload["status"] != "VERIFIED"


def test_offline_suite_never_enables_live_or_writes_live_capability() -> None:
    """AST guard against the T103 REJECT pattern.

    Forbidden in any stockdb offline test module:
    - keyword allow_live=True
    - writing a path/name containing live_capability
    - this module calling .probe(
    """
    for path in TESTS.glob(f"{STOCKDB_TEST_PREFIX}*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "allow_live":
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    raise AssertionError(
                        f"{path.name}: allow_live set to True is forbidden in offline suite"
                    )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"write_text", "write_bytes"}:
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            if "live_capability" in arg.value:
                                raise AssertionError(
                                    f"{path.name}: must not write live_capability artifact"
                                )
                    if path.name == "test_stockdb_live_capability.py":
                        raise AssertionError("test_stockdb_live_capability must not write files")
        if path.name == "test_stockdb_live_capability.py":
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "probe"
                ):
                    raise AssertionError("test_stockdb_live_capability must not call .probe")
        elif "live_capability" in source:
            raise AssertionError(f"{path.name}: must not reference live_capability")


def test_default_settings_disallow_live() -> None:
    from tvchan.infrastructure.market.stockdb import StockDBSettings

    settings = StockDBSettings()
    assert settings.allow_live is False
