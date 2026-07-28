# Migration Inventory

This inventory is deliberately sequenced. A row is not permission to migrate immediately.

| Wave | Item | Source evidence | Destination | Classification | Dependency | Exit criterion |
|---|---|---|---|---|---|---|
| 1 | canonical Bar | `domain/models.py:RawBar`, `schemas/market.py:BarDTO` | `domain.market` | refactor before migration | target domain rules | immutable value model, adjustment/time semantics covered |
| 1 | market port | `infra/market/gateway.py` | `application.ports` | wrap behind adapter | Bar contract | fake adapter and contract tests |
| 1 | SDK/HTTP adapters | `stockdb_client.py`, `stockdb_http_client.py` | `adapters.market` | wrap behind adapter | market port | same behavior for range, normalization, health, timeout |
| 1 | quality gate | `bar_quality.py` | market quality policy | refactor before migration | canonical Bar, daily reference contract | repair/drop/without-reference fixtures pass |
| 1 | range validator | `MarketBarsQuery`, RUNBOOK 3.5 | market query application layer | retain as-is with evidence | API input boundary | missing `end` fails explicitly |
| 1 | market health | `api/health.py`, gateway health methods | target readiness model | refactor before migration | adapter health | liveness independent; readiness dependency-aware |
| 2 | Chan port | `infra/chan/chan_engine.py` | `application.ports.ChanEnginePort` | wrap behind adapter | normalized bars | domain has no chan.py imports |
| 2 | chan.py adapter | `chan_adapter.py`, external `D:\chan.py-main` | `adapters.chanpy` | wrap behind adapter | Chan port | full/step modes and mapping fixtures |
| 2 | half profile | `settings.py`, `ChanEngine._build_config` | target config | retain as-is with evidence | profile schema | half default; strict explicit comparison only |
| 2 | Chan DTOs | `serializers.py`, schemas | domain/publication DTO | refactor before migration | Chan output mapping | confirmed/predictive and stable IDs validated |
| 2 | golden | `tests/golden`, `golden_snapshot.py` | target tests/fixtures | migrate tests/fixtures only | Chan adapter + canonical fixtures | old/new diff reviewed; no silent baseline rewrite |
| 3 | snapshot identity | `SnapshotService` hash/version seed | publication context | refactor before migration | Bar + quality + config | reproducible ID includes input/config/quality |
| 3 | checkpoint | `ChanIncrementalEngine`, repository checkpoint methods | publication application service | refactor before migration | snapshot and Chan port | replay from checkpoint deterministic |
| 3 | published head | `PublishHeadService`, `save_head` | publication domain/repository | refactor before migration | snapshot and publication transaction | atomic current head and stale semantics |
| 3 | SQLite repository | `chan_state_repository.py` | persistence adapter | refactor before migration | target schema/backup policy | migration cannot drop live state; rollback tested |
| 3 | projection | serializer projection/display methods | projection application service | refactor before migration | DTO and timeframe mapping | cross-level anchor fixtures pass |
| 3 | read API | `api/market.py`, `api/chan.py` GET routes | target API adapter | refactor before migration | ports and DTOs | view/head read-only and no compute side effect |
| 4 | TV datafeed | `tv-datafeed.ts` | target presentation adapter | defer to later wave | read API contract | cache/range/browser matrix |
| 4 | overlay renderer | `overlay-manager.ts`, render order | target presentation | defer to later wave | projection DTO | visual and object-level acceptance |
| 4 | visibility/style | `overlay-style-panel.ts` | target UI state | defer to later wave | renderer | local persistence and per-level visibility |
| 5 | realtime writer/runtime | `live_market.py`, `live_runtime.py` | operations/application | defer to later wave | stable market adapter and event model | bounded recovery, no adjusted raw writes |
| 5 | replay/lifecycle | `replay_service.py`, replay repository, archive evidence | replay/lifecycle context | defer to later wave | checkpoint, stable IDs, event model | deterministic event stream and storage |
| 5 | strategy/backtest | `strategy/` | strategy/backtest contexts | defer to later wave | replay/lifecycle and deep daily/weekly data | isolated deterministic backtest evidence |

## Migration gates

1. No Wave 2 work until Wave 1 Bar/market contracts and dependency tests pass.
2. No publication migration until snapshot identity, checkpoint and head semantics are explicit.
3. No TradingView migration until read-only API contracts are stable.
4. No lifecycle/strategy migration into the main chart path.
5. Every migrated capability needs an old/new comparison fixture or an explicit reason why comparison is impossible.
6. Every storage change has a safe migration, backup, dry run and rollback story.
