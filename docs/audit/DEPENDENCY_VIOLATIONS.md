# Dependency Violations and Migration Risks

These are observations against the target rules, not claims that the legacy system is unusable.

| Severity | Violation/risk | Evidence | Impact | Required mitigation |
|---|---|---|---|---|
| Critical | External `chan.py` modules are imported by infrastructure/runtime | `infra/chan/chan_engine.py`, `chan_adapter.py` use `import_module` and external path bootstrap | Domain and application contracts cannot be tested independently | define `ChanEnginePort`; keep imports in adapter only |
| Critical | SDK client is a process/global-lifecycle concern | `infra/market/stockdb_client.py`, gateway factory and settings path bootstrap | stale client/timeout failures can split market and Chan views | adapter-owned lifecycle, timeout, reconnect policy and readiness |
| Critical | SQLite repository owns schema initialization and publication storage | `infra/storage/chan_state_repository.py` | migration can destroy live state; historical v2 DDL caused DROP risk | target persistence port, explicit migration, backup and rollback tests |
| High | FastAPI schemas and routes are the direct composition boundary | `api/*.py`, `schemas/*.py` | target domain would absorb framework DTOs if copied | map API DTOs at adapter/application edge |
| High | Serializer produces frontend-oriented projection DTOs | `infra/chan/serializers.py` | calculation/domain output becomes coupled to display timeframe | separate domain snapshot from projection mapper |
| High | Snapshot service aggregates, quality-checks and hashes in one service | `infra/market/snapshot_service.py` | policy, data access and identity changes become coupled | split market acquisition, quality policy and snapshot identity |
| High | Version semantics are split across engine, Chan head, market head and DB rows | `chan_incremental.py`, repository heads/checkpoints | stale or rollback decisions can use incompatible versions | define typed input/config/run/publication versions; no numeric ordering assumptions before ADR |
| High | Live writer can write raw StockDB state | `services/live_market.py` | adjusted prices could contaminate source data | enforce `none` at command, adapter and write layers |
| Medium | Broad exception handling can turn unavailable quality reference into pass-through | `snapshot_service.py` catches reference errors and returns base bars | hidden data-quality blind spots | explicit degraded quality state and readiness/observability |
| Medium | Frontend datafeed caches market head and bars | `frontend/src/tradingview/datafeed/tv-datafeed.ts` | stale history may appear valid after correction | cache key/version invalidation and cold-session acceptance |
| Medium | Overlay manager combines query, filtering, entity lifecycle and rendering order | `frontend/src/tradingview/overlay/overlay-manager.ts` | difficult unit testing and cross-level regressions | split query client, projection filter and renderer |
| Medium | Replay storage is a second SQLite schema and event model | `infra/replay/repository.py`, `replay_service.py` | replay/lifecycle can diverge from publication identity | defer; define event contract before migration |
| Medium | Configuration defaults are environment-driven and external-path dependent | `settings.py`, `bootstrap_external_paths` | runtime differs by host; target Wave 0 cannot reproduce it | typed target config and explicit dependency injection |
| Low | Scripts are executable operational policy outside application contracts | `backend/scripts/*.py` | scripts can bypass safeguards or drift from services | migrate individually with dry-run and fixture evidence |
| Low | Historical docs mix verified runtime facts and plans | `docs/**`, archive transcript | stale decisions can be treated as current | preserve evidence labels and use PROJECT.md corrected state |

## Non-violations to preserve

- The legacy frontend formal path is read-only (`market/*` and `chan/view`); it must remain so in the target.
- The production profile is already corrected to half; do not reopen it.
- `free-stockdb` and Chan application state are separated conceptually even though the legacy composition is not yet target-isolated.
- Golden snapshots intentionally exclude stable IDs, which supports an ID scheme migration without hiding numerical/structural differences.
