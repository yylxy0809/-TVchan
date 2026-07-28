# ADR-Market-001: Canonical Market Identity and Time

## Status

Accepted for Wave 1.

## Decision

- A-share only: canonical `Symbol` is `SSE:<six-digit-code>` or `SZSE:<six-digit-code>`; provider symbols are adapter-only.
- Canonical timeframes: `1m, 5m, 15m, 30m, 60m, 1d, 1w, 1mo`. `1M` is only an adapter alias for `1mo`; unsupported frequencies fail.
- Identity is `(symbol, timeframe, open_time, adjustment)`; `open_time` is timezone-aware period start. Compare/persist as UTC instant; `trading_date` is Asia/Shanghai.
- Daily bars start at 09:30 Asia/Shanghai; weekly/monthly bars start at 09:30 on their first trading day. Ranges are half-open `[start, end)`.
- Exact duplicates collapse; same identity with different values is `DUPLICATE_CONFLICT`. Last-write-wins is forbidden.

## Consequences

Adapters normalize legacy naming and timestamps before returning domain values. A gap requires calendar/session evidence.
