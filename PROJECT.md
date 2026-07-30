# TVchan Project Command Brief

> **当前状态入口：** [PROJECT_STATE.md](PROJECT_STATE.md) 记录已合并事实、活动候选、外部风险和新窗口接管步骤。本文件保留架构命令简报；两者冲突时，以较新的已证实 Git/PR 事实为准，并更新状态档案。

Version: 1.0.0  
Status: Architecture rebuild active

## 1. Repository Roles

### Legacy source project

- Local path: `D:\TV`
- GitHub: `https://github.com/yylxy0809/tv`
- Role: verified capability source, regression baseline, fixtures, scripts and migration reference
- Rule: read-only by default; do not implement the new architecture in this repository

### New target project

- Recommended local path: `D:\TVchan`
- GitHub: `https://github.com/yylxy0809/-TVchan`
- Role: the only target repository for the redesigned architecture

The rebuild is not a bulk copy of `D:\TV`. Establish the target architecture first, then migrate capabilities one by one with contract tests and old/new comparisons.

## 2. Current Verified Legacy Baseline

At legacy HEAD `fa99ef5c8b071ca33b912a8391478dfca58fe7a3`:

- branch: `main`, aligned with `origin/main`
- worktree: clean
- backend: `79 passed, 4 skipped`
- frontend: Vite build passed
- stockdb runtime: unavailable during the latest audit (`127.0.0.1:7899` timeout)

Passing tests prove controlled code paths only; they do not prove the external data runtime is currently healthy.

## 3. Corrected Decision State

The following are current decisions, not open questions:

- `chan.py` remains the calculation kernel and must be isolated behind an adapter
- the production Bi profile is `half`
- `bi_fx_check=half`
- `bi_allow_sub_peak=false`
- `strict` is retained only for comparison and regression
- this profile was confirmed, regression-tested, republished and adopted on 2026-07-27
- TradingView is a read-only presentation client
- frontend requests must never trigger Chan calculations
- `free-stockdb` stores market bars, not Chan application state
- lifecycle/replay data must not become a dependency of the main chart
- current main chart scope is Bi, ZS and BSP; Seg is not a required chart layer

Any older document describing the Bi profile as awaiting user approval is stale.

## 4. Target Architecture

Use the architecture documents under `docs/` as the governing source.

Target dependency direction:

```text
Presentation
    -> Application
        -> Domain
            <- Ports
                <- Infrastructure / Adapters
```

Primary bounded contexts:

- Market
- Chan Analysis
- Publication / Snapshot
- Strategy
- Backtest
- Operations / Observability

## 5. Initial Project Structure

```text
TVchan/
├── PROJECT.md
├── AGENTS.md
├── pyproject.toml
├── backend/
│   ├── src/tvchan/
│   │   ├── domain/
│   │   │   ├── market/
│   │   │   ├── chan/
│   │   │   └── publication/
│   │   ├── application/
│   │   │   ├── commands/
│   │   │   ├── queries/
│   │   │   └── ports/
│   │   ├── infrastructure/
│   │   │   ├── persistence/
│   │   │   └── messaging/
│   │   ├── adapters/
│   │   │   ├── market/
│   │   │   ├── chanpy/
│   │   │   └── api/
│   │   └── bootstrap/
│   └── tests/
├── frontend/
├── docs/
│   ├── ADR/
│   └── audit/
└── scripts/
```

This is a starting boundary, not permission to create empty speculative abstractions.

## 6. Migration Order

Wave 0: engineering skeleton

- package and dependency management
- test runner
- lint/type-check baseline
- configuration loading
- dependency boundary tests
- CI

Wave 1: market data contract

- canonical `Bar`
- `MarketDataGateway` port
- StockDB adapter
- time range validation
- market health model

Wave 2: Chan calculation boundary

- `ChanEnginePort`
- `ChanPyAdapter`
- explicit half/strict profiles
- normalized domain DTOs
- golden and contract comparison

Wave 3: publication/query chain

- snapshot
- published head
- projection
- read-only API

Wave 4: TradingView migration

- datafeed
- overlay query client
- rendering layers
- browser acceptance matrix

Wave 5: real-time, lifecycle, strategy and backtest

These are forbidden from entering earlier waves unless an accepted ADR changes the order.

## 7. Agent Roles

### Codex CLI

Owns the target repository engineering skeleton and executable implementation work.

### Grok Build

Owns independent architecture review, legacy-to-target mapping, risk discovery and acceptance review.

### Foreman

Owns architecture decisions, task sequencing, cross-agent conflict resolution and acceptance.

## 8. Mandatory Working Rules

- Do not modify `D:\TV` unless a later task explicitly authorizes it
- Do not copy the old backend wholesale
- Do not rewrite `chan.py`
- Do not import infrastructure packages from the domain layer
- Do not let FastAPI or TradingView types enter domain models
- Do not create future strategy/backtest abstractions during Wave 0
- Every migration must include tests and evidence
- Every external dependency must be behind a port/adapter
- Keep commits small and scoped
- Record architectural deviations as ADRs before implementation

## 9. Definition of Done for Wave 0

- new repository cloned to `D:\TVchan`
- backend package imports successfully
- unit tests execute successfully
- lint and type checks execute successfully
- dependency direction is enforced by tests or tooling
- minimal health endpoint works without StockDB or chan.py
- no business calculation has been copied yet
- README contains local setup instructions
- CI executes the same verification commands
