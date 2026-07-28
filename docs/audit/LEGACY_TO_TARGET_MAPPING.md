# Legacy to Target Mapping

## Mapping rules

The target architecture is governed by `PROJECT.md` and `docs/01_SYSTEM_ARCHITECTURE_V2.md`: Presentation → Application → Domain, with Infrastructure/Adapters implementing ports. Legacy paths are evidence sources, not copy instructions.

| Legacy capability | Legacy path/symbols | Target boundary | Classification | Migration proof |
|---|---|---|---|---|
| Bar model | `backend/app/domain/models.py:RawBar`, `schemas/market.py:BarDTO` | `domain.market.Bar` | refactor before migration | value/adjustment/time contract tests |
| Market gateway | `infra/market/gateway.py:MarketDataGateway` | `application.ports.MarketDataGateway` + `adapters.market` | wrap behind adapter | fake port contract + StockDB adapter integration |
| SDK provider | `infra/market/stockdb_client.py:StockDBGateway` | `adapters.market.StockDbSdkAdapter` | wrap behind adapter | timeout, health, range and normalization tests |
| HTTP provider | `infra/market/stockdb_http_client.py:StockDBHttpGateway` | alternate market adapter | wrap behind adapter | same port contract; provider parity fixture |
| Live writer | `services/live_market.py:StockDbLiveWriter` | application command + write adapter | wrap behind adapter | none/qfq write guard and idempotency tests |
| Quality gate | `infra/market/bar_quality.py:ExDivTailBarGuard` | market quality policy | refactor before migration | real defect fixtures; repair/drop report contract |
| Range validation | `schemas/market.py:MarketBarsQuery`, RUNBOOK 3.5 | application query validation | retain as-is with evidence | `start` requires `end`; no silent empty query |
| Snapshot | `infra/market/snapshot_service.py:SnapshotService` | `domain.publication` / application snapshot service | refactor before migration | snapshot ID/config/quality reproducibility |
| Chan adapter | `infra/chan/chan_adapter.py:ChanAdapter` | `adapters.chanpy` | wrap behind adapter | normalized input and frequency mapping tests |
| Chan engine | `infra/chan/chan_engine.py:ChanEngine` | `application.ports.ChanEnginePort` + adapter | wrap behind adapter | half golden, strict comparison only |
| Profile config | `settings.py:CHAN_BI_PROFILES`, `ChanBiProfile` | target configuration/application | retain as-is with evidence | fixed half default and explicit strict compare profile |
| Serializer | `infra/chan/serializers.py:ChanSerializer` | domain DTO mapper/projection service | refactor before migration | DTO schema and stable identity tests |
| Stable identity | serializer `ID_SCHEME = "v2"` | domain identity policy | retain as-is with evidence | same structure maps to same ID; price changes are updates |
| Projection anchors | serializer projection/display methods | application projection boundary | refactor before migration | cross-level endpoint fixtures |
| Incremental engine | `services/chan_incremental.py:ChanIncrementalEngine` | application publication command | refactor before migration | checkpoint/replay/publish atomicity tests |
| SQLite state | `infra/storage/chan_state_repository.py` | persistence port + infrastructure repository | refactor before migration | schema safety, backup, migration tests |
| Replay storage | `infra/replay/repository.py:ReplayRepository` | later replay context | defer to later wave | fixed input replay fixture |
| API read chain | `api/market.py`, `api/chan.py` | target query handlers and API adapter | refactor before migration | read-only view/head contract tests |
| API compute/replay | `api/chan.py` POST routes | application commands; not frontend path | defer/retarget | explicit authorization and side-effect tests |
| TV datafeed | `frontend/src/tradingview/datafeed/tv-datafeed.ts` | Wave 4 presentation adapter | defer to later wave | browser datafeed contract and cache tests |
| Overlay manager | `frontend/src/tradingview/overlay/overlay-manager.ts` | Wave 4 presentation renderer | defer to later wave | render ordering and visibility acceptance |
| Style panel | `overlay-style-panel.ts` | Wave 4 UI state | defer to later wave | local persistence and level visibility tests |
| Live runtime | `services/live_runtime.py` | Wave 5 operations/application | defer to later wave | bounded recovery and observability tests |
| Strategy features | `strategy/features/*` | Wave 5 Strategy domain | defer to later wave | domain-only feature tests |
| Backtest | `strategy/backtest/*` | Wave 5 Backtest application | defer to later wave | replay-backed deterministic tests |
| Golden fixtures | `backend/tests/golden/*`, `golden_snapshot.py` | target contract/regression fixtures | migrate tests/fixtures only | old/new comparison with config hash |
| Runtime scripts | `backend/scripts/*` | target scripts one by one | migrate tests/fixtures only | each script has owner, inputs, outputs and safety mode |

## Target ownership by wave

- **Wave 0:** package, config, boundary checks, CI, health only. No legacy business implementation.
- **Wave 1:** `Bar`, market port, StockDB adapter, time validation, health/readiness model.
- **Wave 2:** Chan port/adapter, half profile, normalized DTOs, golden comparisons.
- **Wave 3:** snapshot, checkpoint, published head, projection and read-only API.
- **Wave 4:** TradingView datafeed, overlay query and browser acceptance.
- **Wave 5:** realtime, lifecycle, replay, strategy and backtest.

## Non-mappings

Do not copy `D:\TV\backend` wholesale, import FastAPI/TradingView types into domain models, or make frontend requests invoke Chan computation. Do not move the external `D:\chan.py-main` tree into the legacy repository during this audit.
