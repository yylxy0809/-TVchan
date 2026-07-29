# ADR-Market-002: Adjustment and Raw-data Semantics

## Status

Accepted for Wave 1.

## Context

Adjustment semantics and numeric precision must be stable across SDK and HTTP adapters. Raw market storage is not application state.

## Decision

- Adjustment is explicit: `NONE`, `QFQ`, or `HFQ`; default `NONE`. Market data is read-only and never written back.
- Domain prices are `Decimal`, retain source precision, never pass through `float`, and serialize as strings.
- Repairs quantize only by rule, using `ROUND_HALF_UP`; scale is provenance.
- Daily adjustment factors use only `NONE` daily bars: `next_day.pre_close / current.close`.
- Private SDK helpers `_apply_fq_in_memory` and `_merge_*` are forbidden. Unsupported combinations fail explicitly.

## Rejected Alternatives

- Implicit adjustment or float conversion: rejected because both conceal meaning and precision loss.
- Private SDK helpers: rejected because they are not a stable provider contract.
- Writing adjusted bars back: rejected because it contaminates raw data.

## Consequences

SDK and HTTP adapters use public, testable provider behavior only.

## Validation

Parity fixtures cover public SDK/HTTP behavior, Decimal serialization, explicit adjustment, factor provenance, and unsupported combinations.
