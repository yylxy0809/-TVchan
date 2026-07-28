# ADR-Market-004: Dependency Health Contract

## Status

Accepted for Wave 1.

## Decision

- `/health` is liveness only: no StockDB, Chan, or quality call.
- `/ready` uses a timeout-bounded probe and returns `READY`, `DEGRADED`, or `NOT_READY`.
- `READY`/`DEGRADED` map to HTTP 200; `NOT_READY` maps to HTTP 503.
- Provider unavailable, timeout, and protocol failures are `NOT_READY`.
- Wave 1 has no probe cache. Status includes provider, checked-at, latency, and safe error code only.

## Consequences

Liveness remains available during dependency outage; readiness reports dependency truth without leaking credentials.
