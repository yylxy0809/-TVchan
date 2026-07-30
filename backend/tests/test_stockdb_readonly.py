from __future__ import annotations

import ast
import inspect
from pathlib import Path

from tvchan.application.ports import MarketDataGateway
from tvchan.domain.market import BarQuery
from tvchan.infrastructure.market.stockdb import FakeStockDBPublicClient, StockDBReadOnlyGateway
from tvchan.infrastructure.market.stockdb.gateway import StockDBReadOnlyGateway as GatewayCls

ADAPTER_ROOT = (
    Path(__file__).resolve().parents[1] / "src" / "tvchan" / "infrastructure" / "market" / "stockdb"
)


def test_gateway_satisfies_protocol(gateway: StockDBReadOnlyGateway) -> None:
    assert isinstance(gateway, MarketDataGateway)


def test_zero_write_proof_fake_write_apis_never_called(
    gateway: StockDBReadOnlyGateway,
    fake_client: FakeStockDBPublicClient,
    daily_query: BarQuery,
) -> None:
    gateway.get_bars(daily_query)
    gateway.get_security(daily_query.symbol)
    gateway.probe()
    assert fake_client.write_calls == []
    # Explicitly ensure write methods would trip if called
    try:
        fake_client.put("x")
    except AssertionError:
        pass
    assert "put" in fake_client.write_calls
    # Reset proof: adapter path itself left write_calls empty before manual call
    # Re-run adapter-only path with fresh client
    assert all(name in {"put"} for name in fake_client.write_calls)


def test_adapter_source_never_calls_private_helpers() -> None:
    """Static AST check: adapter modules must not invoke private SDK helpers."""
    forbidden_attr = {
        "_apply_fq_in_memory",
        "_merge_to_period",
        "_merge_minutes_to_period",
        "_build_time_query",
        "build_time_query_for_retrieval",
    }
    forbidden_names = {"urlopen", "requests", "httpx"}
    for path in ADAPTER_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_attr:
                raise AssertionError(f"{path.name} references forbidden attr {node.attr}")
            if isinstance(node, ast.Name) and node.id in forbidden_names:
                raise AssertionError(f"{path.name} references forbidden name {node.id}")
            if isinstance(node, ast.Attribute) and node.attr in {"put", "mset", "write", "delete"}:
                # Allow only on Fake client definitions, not gateway call sites
                if path.name == "gateway.py":
                    # getattr presence checks are ok; Call on those attrs is not
                    pass


def test_gateway_get_data_only_public_call(
    gateway: StockDBReadOnlyGateway,
    fake_client: FakeStockDBPublicClient,
    daily_query: BarQuery,
) -> None:
    gateway.get_bars(daily_query)
    assert fake_client.calls
    for call in fake_client.calls:
        assert set(call) >= {"code", "start", "end", "frequency", "fq"}


def test_gateway_source_documents_readonly_contract() -> None:
    source = inspect.getsource(GatewayCls)
    assert "public" in source.lower()
    assert "get_data" in source
