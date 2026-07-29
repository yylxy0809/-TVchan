# Wave 1 Market Contract

## Scope

This is Wave 1 implementation admission. It permits canonical market data, ports, StockDB adapters, quality, and health/readiness only. It does not permit Chan, snapshot, publication, TradingView, writer, replay, lifecycle, strategy, or backtest.

`docs/audit/WAVE_1_RECOMMENDATION.md` is a legacy-audit/risk baseline, not this implementation contract.

## Boundary

PROJECT.md is authoritative: Presentation/API -> Application -> Domain; Application -> Ports <- Adapters/Infrastructure; Bootstrap composes implementations. Domain/Application may not import FastAPI, StockDB SDK, HTTP/database clients, or adapters. The dependency-boundary script must grow with Wave 1 code.

## Canonical data

`Symbol`: `SSE:<six-digit-code>` or `SZSE:<six-digit-code>`; provider symbols are adapter-only.
`Timeframe`: `1m, 5m, 15m, 30m, 60m, 1d, 1w, 1mo`; only adapter input maps `1M -> 1mo`.
Immutable `Bar`: symbol, timeframe, timezone-aware open_time, Asia/Shanghai trading_date, explicit adjustment, positive Decimal OHLC, optional non-negative Decimal volume/amount, optional daily pre_close, and separate provenance. It satisfies `low <= min(open, close) <= max(open, close) <= high`.

Daily open_time is 09:30 Asia/Shanghai; weekly/monthly is 09:30 on first trading day. Identity is `(symbol, timeframe, open_time, adjustment)`; output is sorted; exact duplicates collapse and conflicting duplicates are `DUPLICATE_CONFLICT`. Ranges are `[start, end)`. Adjustment `NONE/QFQ/HFQ` is explicit, default `NONE`. Decimal serializes as string without construction-time quantization.

## Port and errors

`MarketDataGateway` owns:

- `get_bars(query: BarQuery) -> RetrievedBars`
- `get_security(symbol: Symbol) -> Security | None`
- `probe() -> DependencyHealth`

`TradingCalendarPort` owns `list_trade_days(range: DateRange) -> tuple[date, ...]`; it may later add session queries. It is deliberately independent of StockDB.

`BarQuery` is canonical and bounded. `RetrievedBars` has sorted bars and retrieval provenance, not a quality claim. Stable errors: `INVALID_QUERY`, `UNSUPPORTED_TIMEFRAME`, `SYMBOL_NOT_FOUND` (no retry); `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT` (retry); `PROVIDER_PROTOCOL_ERROR`, `NORMALIZATION_ERROR`, `DUPLICATE_CONFLICT` (no retry). Quality degradation is a result state. Logs contain no credentials, credential URLs, or raw payloads.

## Adapter, quality, health

SDK/HTTP implement the port only; typed settings are Bootstrap-injected. They use public provider behavior only: private SDK adjustment/merge helpers are forbidden, unsupported combinations fail, and raw data is never written back.

`QualityPolicy` receives target bars, same-adjustment daily references, `NONE` daily factor bars, and calendar data. It returns qualified bars, `QualityStatus`, `CompletenessStatus`, report, and provenance. `QualityStatus` is `VALIDATED|DEGRADED|REJECTED`; `CompletenessStatus` is `COMPLETE|INCOMPLETE|UNKNOWN`. Missing calendar means completeness `UNKNOWN` and quality at least `DEGRADED`; missing daily reference preserves bars as `DEGRADED`; gaps are never filled; repairs/drops retain provenance and use `next_day.pre_close / current.close` with `ROUND_HALF_UP` scale.

`/health` is liveness only. `/ready` calls a timeout-bounded probe: `READY/DEGRADED` is HTTP 200; `NOT_READY` is HTTP 503. No probe cache. `MarketDataQueryService` validates, retrieves, deduplicates, acquires references/calendar, assesses quality, and assembles results. It creates no snapshot, invokes no Chan, persists no application state, and exposes no HTTP. Wave 1 adds no public market endpoint.

## Test matrix and gate

| Area | Required evidence |
|---|---|
| Domain | Decimal/OHLC, identity, time conversion, sorting, duplicate collapse/conflict |
| Symbol/timeframe | legacy normalization, canonical set, invalid code, unsupported failure |
| Ports | MarketDataGateway and TradingCalendarPort isolation, bounded range, typed errors, empty vs unavailable, timeout/protocol |
| SDK/HTTP | public-capability parity, provenance/errors, no write/private calls |
| Quality | separate quality/completeness states, repair, drop, missing-reference degradation, gap, factor/provenance |
| Application/DI | order, forbidden imports, liveness, readiness |
| Regression | legacy fixtures; CI green without StockDB |

Admission requires this matrix, pytest, ruff, mypy, and dependency-boundary checks green. Live parity is captured when provider is available or explicitly reported unavailable.
