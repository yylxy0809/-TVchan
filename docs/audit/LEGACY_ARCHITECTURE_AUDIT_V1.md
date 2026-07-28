# Legacy Architecture Audit V1

- **Legacy source:** `D:\TV`
- **Target:** `D:\TVchan` / `yylxy0809/-TVchan`
- **Audit mode:** read-only inspection; no legacy code or data modified
- **Evidence date:** 2026-07-28
- **Evidence labels:** **Verified fact** = directly observed in source tree, tests, committed artifacts, or documented commands; **Architectural inference** = interpretation of verified structure; **Open question** = requires a fresh runtime or target-side decision.

## Executive conclusion

`D:\TV` is a working vertical slice, not a suitable bulk-copy source. It has a verified market-to-Chan-to-publication-to-TradingView path, useful tests, golden fixtures, recovery scripts, and operational evidence. It also couples external SDK imports, FastAPI composition, SQLite state, and frontend rendering more tightly than the target architecture permits. The safe migration unit is a contract plus adapter and comparison tests, not a directory.

The current production Bi decision is **half**: `bi_fx_check=half`, `bi_allow_sub_peak=false`; `strict` is comparison/regression only. This audit does not reopen that decision.

## Capability inventory

| Area | Legacy evidence | Classification | Target owner/boundary |
|---|---|---|---|
| Canonical market bars | `backend/app/domain/models.py`, `schemas/market.py` | refactor before migration | `domain.market` `Bar`; Wave 1 contract |
| StockDB read gateway | `infra/market/gateway.py`, `stockdb_client.py`, `stockdb_http_client.py` | wrap behind adapter | `adapters.market` implementing `MarketDataGateway` |
| StockDB write path | `services/live_market.py`, `live_provider_adapter.py` | wrap behind adapter; restrict writes | application command + market adapter; no domain dependency |
| Quality gate | `infra/market/bar_quality.py`, `snapshot_service.py` | retain as-is with evidence, then refactor into domain policy/port | market quality policy/application service |
| Time-range validation | `schemas/market.py`, `RUNBOOK.md` three-point-five | retain behavior; refactor contract location | market query validation |
| Chan invocation | `infra/chan/chan_engine.py`, `chan_adapter.py` | wrap behind adapter | `adapters.chanpy.ChanEnginePort` |
| Serialization | `infra/chan/serializers.py` | refactor before migration | domain snapshot DTO + projection mapper |
| Half/strict profiles | `settings.py`, `chan_engine.py`, profile tests | retain as-is with evidence | application config port; fixed half production default |
| Stable IDs | `serializers.py` ID scheme v2 | retain as-is with evidence | domain identity policy |
| Projection/display anchors | `serializers.py` projection/display methods | refactor before migration | application projection service + DTO mapper |
| Snapshot/checkpoint | `snapshot_service.py`, `chan_incremental.py`, storage repository | refactor before migration | publication/snapshot bounded context |
| Published head/version | `chan_incremental.py`, `chan_state_repository.py`, `live_state_query.py` | refactor before migration | `domain.publication` + repository port |
| FastAPI routes | `api/market.py`, `api/chan.py`, `api/health.py`, `api/strategy.py` | migrate tests/fixtures first; rewrite adapters | target presentation/bootstrap |
| SQLite state | `infra/storage/chan_state_repository.py`, replay repository | refactor before migration | infrastructure persistence behind ports |
| TradingView datafeed | `frontend/src/tradingview/datafeed/tv-datafeed.ts` | defer to Wave 4; migrate tests/fixtures first | target presentation adapter |
| Overlay rendering | `overlay-manager.ts`, `overlay-style-panel.ts`, `render-order.ts` | defer to Wave 4 | target frontend presentation |
| Configuration | `settings.py`, environment variables | refactor before migration | target configuration/bootstrap |
| Global/external state | SDK client lifecycle, `settings.bootstrap_external_paths()` | dependency violation; refactor before migration | composition root and adapter lifecycle |
| Exception/logging | gateway/quality/live runtime logging and broad catches | refactor before migration | target error taxonomy/observability |
| Scripts | `backend/scripts/*.py` | migrate tests/fixtures only initially | target tooling, each script re-owned explicitly |
| Golden snapshots | `backend/tests/golden`, `golden_snapshot.py` | migrate tests/fixtures only | contract/regression suite |
| Replay/lifecycle | `replay_service.py`, replay DB, archive evidence | defer to later wave | Wave 5 application contexts |
| Strategy/backtest | `strategy/`, `api/strategy.py` | defer to later wave | Wave 5 strategy/backtest contexts |

## Runtime boundary

Verified flow:

```text
StockDB SDK/HTTP -> MarketDataGateway -> SnapshotService -> ChanEngine/chan.py
-> serializer -> ChanStateRepository/published head -> read API -> TradingView datafeed/overlay
```

The target must preserve the observable contracts while replacing direct imports with ports and adapters. The target Wave 0 currently exposes only an independent health endpoint and dependency-boundary checks; that is intentional and is not evidence that legacy capabilities are already migrated.

## Evidence limitations

- Legacy documentation records historical runtime claims; current external StockDB health must be rechecked before migration acceptance.
- `chan.py` remains outside the legacy repository and must not be modified as part of this audit.
- A public GitHub target issue defines the migration deliverables, but does not substitute for target-side contract tests.
