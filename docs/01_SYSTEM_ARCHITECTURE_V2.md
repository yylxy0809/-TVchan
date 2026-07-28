# System Architecture V2

## Purpose

定义 Chan Theory Quantitative Platform 长期演进架构。

## Architecture Principles

- Domain First
- Interface First
- Event Driven
- Adapter Isolation
- Single Source Of Truth
- Incremental Evolution

## Layers

### Presentation Layer

负责 TradingView、Web 管理后台展示。

禁止：
- 计算缠论
- 直接访问数据库

### Application Layer

负责业务流程编排：

- Query Service
- Command Service
- Strategy Service
- Backtest Service

### Domain Layer

核心领域：

- Market Domain
- Chan Domain
- Strategy Domain
- Signal Domain

### Infrastructure Layer

提供：

- Database
- Repository
- Cache
- Storage

### Adapter Layer

隔离外部系统：

- StockDB
- TradingView
- Exchange API
- AI Provider

## Dependency Rule

PROJECT.md 是依赖方向的最高准据：

Presentation / API -> Application -> Domain
Application -> Ports <- Adapters / Infrastructure
Bootstrap composes implementations

Domain 不依赖 FastAPI、TradingView、StockDB、SDK、HTTP 客户端、数据库或 Infrastructure。Application 负责用例编排，并只通过 Ports 访问外部能力。Adapters / Infrastructure 实现 Ports；Bootstrap 是唯一装配位置。

依赖边界脚本是可执行护栏。新增 Wave 1 代码时必须扩展其覆盖范围，不能以文档说明替代测试。

## Core Runtime Flow

External Market
→ Provider Adapter
→ Market Domain
→ Chan Engine
→ Snapshot Publisher
→ API
→ TradingView
