# ADR-Market-003: Quality and Completeness Policy

## Status

Accepted for Wave 1.

## Decision

- Quality returns `VALIDATED`, `DEGRADED`, or `REJECTED`, with immutable report and per-record provenance.
- Missing calendar means completeness `UNKNOWN` and at least `DEGRADED`.
- Missing same-adjustment daily reference preserves bars but is `DEGRADED`, never `VALIDATED`.
- Gaps are reported, never filled, and use calendar/session evidence.
- Repair/drop provenance records identity, reason, factor, before/after, and reference identity. Invalid/unrepairable bars are dropped with provenance.
- Repair rounding is `ROUND_HALF_UP`; scale is provenance.

## Consequences

Wave 2 must not treat degraded data as validated input. Quality is a domain policy, not a gateway method.
