# Wave 1 Recommendation

## Recommendation

Implement only the **market data contract boundary** in Wave 1. Do not migrate Chan computation, publication storage, TradingView, replay, lifecycle, strategy or backtest in the same wave.

This is the narrowest wave that creates a reusable foundation while protecting the verified legacy behavior.

## Scope

### 1. Canonical `Bar`

Create the target domain Bar with timestamp, OHLCV, symbol/frequency and explicit adjustment semantics. Keep framework and StockDB row types outside the domain.

Acceptance:

- immutable/value-oriented model;
- OHLCV validation is explicit;
- `none`/`qfq` are represented as a query/read concern, not silently mixed into raw storage;
- serialization tests cover timezone and source-time normalization.

### 2. `MarketDataGateway` port

Define a small application port for bars, trade days, security metadata and health. Require explicit range semantics: a supplied `start` requires a supplied `end` or an explicit bounded policy.

Acceptance:

- fake adapter contract tests;
- empty, malformed and timeout responses are classified errors;
- no target domain import of FastAPI, SDK, `stockdb.pyd` or HTTP client code.

### 3. StockDB adapter, initially read-only

Wrap the legacy SDK/HTTP implementations behind the port. Do not migrate the legacy writer in Wave 1. The adapter must expose provider health, timeout and normalized errors.

Acceptance:

- SDK and HTTP parity fixture for the same bounded query;
- explicit distinction between unavailable provider and empty result;
- no qfq/hfq raw write path exists in the Wave 1 target.

### 4. Quality policy

Port the tested `bar_quality` behavior as a market policy, including repaired/dropped and without-reference counts. Preserve the distinction between daily and bar counts. Do not silently treat a missing daily reference as clean data.

Acceptance:

- real pollution fixture repairs the known three bars;
- invalid/unrepairable bars are dropped;
- missing reference yields a visible degraded report;
- quality result contributes to snapshot/input identity when snapshots arrive in Wave 3.

### 5. Market health/readiness

Keep liveness independent of StockDB, and add a dependency-aware readiness model only after the adapter contract exists.

Acceptance:

- `/health` remains usable without external services;
- readiness distinguishes process alive, provider unavailable, timeout and normalized data failure;
- logs include request/input context without leaking credentials.

## Explicitly out of scope

- `chan.py` adapter and profile migration (Wave 2);
- snapshot/checkpoint/published head/SQLite migration (Wave 3);
- TradingView datafeed and overlays (Wave 4);
- realtime writer/runtime, replay/lifecycle, strategy and backtest (Wave 5);
- changing the production Bi profile (`half`, `bi_fx_check=half`, `bi_allow_sub_peak=false`).

## Required evidence

1. Target unit and contract tests pass.
2. Dependency-boundary script passes.
3. SDK/HTTP parity evidence is captured, or the provider is explicitly marked unavailable rather than faked.
4. Quality fixtures and range validation tests pass.
5. No files outside the Wave 1 target boundary are imported by domain/application tests.
6. A short ADR records adapter ownership, raw-data adjustment semantics and readiness states.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Copying legacy models preserves framework leakage | define target Bar first; map at adapter edge |
| StockDB is unavailable in CI | contract tests use fakes; live integration is separately reported |
| qfq contaminates raw semantics | Wave 1 read-only adapter; reject write APIs until explicit command design |
| quality gate silently passes missing reference | degraded report is a first-class result |
| later Chan work starts before market contract is stable | enforce wave gate in task plan and dependency tests |
| target architecture grows speculative empty packages | create only code required by acceptance tests |

## Definition of done

Wave 1 is complete when the target has a tested canonical Bar, a tested market port, at least one isolated StockDB adapter, explicit range/error/health behavior, quality fixtures, and no domain/infrastructure boundary violations. It must remain independently testable without StockDB or chan.py.
