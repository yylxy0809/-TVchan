# Migration Plan V1

## Strategy

采用渐进式迁移，不推倒现有系统。

## Phase 1 Architecture Foundation

建立：

- domain
- application
- infrastructure
- adapters
- events

冻结核心接口。

## Phase 2 Adapter Migration

迁移：

- chan.py
- free-stockdb
- TradingView
- AI Provider

统一通过 Adapter 接入。

## Phase 3 Domain Isolation

拆离：

- Market Domain
- Chan Domain
- Strategy Domain

## Phase 4 Event Driven

替换模块直接调用。

## Phase 5 Platform Expansion

增加：

- Backtest
- Strategy Marketplace
- AI Analysis
- Automated Trading

## Migration Rules

- 小步提交
- 保持可运行
- 每阶段可回滚
- 优先保护已验证功能
