# ADR-Market-004: Dependency Health Contract

## Status

Accepted for Wave 1.

## Context

Process liveness and provider readiness answer different operational questions. Dependency outage must not make liveness unavailable or leak secrets.

## Decision

- `/health` is liveness only: no StockDB, Chan, or quality call.
- `/ready` uses a timeout-bounded probe and returns `READY`, `DEGRADED`, or `NOT_READY`.
- `READY`/`DEGRADED` map to HTTP 200; `NOT_READY` maps to HTTP 503.
- Provider unavailable, timeout, and protocol failures are `NOT_READY`.
- Wave 1 has no probe cache. Status includes provider, checked-at, latency, and safe error code only.

## Rejected Alternatives

- /health probing StockDB or Chan: rejected because liveness would depend on external services.
- Probe cache in Wave 1: rejected because stale readiness hides current dependency state.
- Raw provider errors or credentials: rejected because observability must be safe.

## Consequences

Liveness remains available during dependency outage; readiness reports dependency truth without leaking credentials.

## Validation

Tests assert liveness has no external call, timeout-bounded readiness mapping, 200/503 responses, and credential/payload redaction.
