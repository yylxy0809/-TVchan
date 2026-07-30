# ADR-Market-005: S1b Quality and Static Calendar Semantics

## Status

Accepted for S1b.

## Decision

`QualityPolicy.assess` accepts daily target bars, same-adjustment daily references, `NONE`
daily factor bars, and either a calendar tuple or `None`. It returns immutable
`QualityAssessment(bars, report)`. `QualityReport.missing_trade_days` is a strictly increasing,
duplicate-free tuple.

All inputs are canonical-identity sorted. Reordered input continues with
`INPUT_REORDERED` and degraded quality; exact duplicates collapse with
`EXACT_DUPLICATE_COLLAPSED` and degraded quality. A conflicting identity in targets,
references, or factor bars rejects with empty output and unknown completeness.

Calendar absence is the only unavailable-calendar condition: it gives unknown completeness and
at least degraded quality. With a calendar, completeness is based on expected calendar dates and
observed qualified dates; gaps populate `missing_trade_days` and are never filled.

For adjusted daily bars, a discontinuity can only be repaired with the same-day reference, the
same-day `NONE` factor bar, and the unique `NONE` bar for the calendar's immediately following
trade day. No later available factor bar may substitute for that next-day bar. Missing evidence
preserves the target and records `INSUFFICIENT_REPAIR_EVIDENCE`. The repair factor is
`next_day.pre_close / current_day.close`, calculated with precision 28 and `ROUND_HALF_UP`, and
quantized to `repair_scale` (0 through 8, default 4). Price fields and non-null `pre_close` are
scaled; volume and amount are unchanged. A repair is accepted only when it exactly equals the
same-adjustment reference; otherwise it is dropped with provenance. `NONE` bars never repair.

`StaticTradingCalendarAdapter` is a no-I/O implementation of `TradingCalendarPort`. A frozen
snapshot has an ISO `YYYY-MM-DD` version, timezone `Asia/Shanghai`, and strictly increasing,
unique trade days. The adapter selects one uniquely versioned snapshot. It returns only dates
whose 09:30 Asia/Shanghai session open lies in the supplied half-open `DateRange`; an end exactly
at 09:30 excludes that date. There is no fallback, cache, or provider error path.

## Consequences

The domain does not import the calendar port. Application code supplies calendar facts. This
slice changes no query service, provider, SDK/HTTP, API, readiness, writer, realtime, Chan,
snapshot, lifecycle, or S2 component.
