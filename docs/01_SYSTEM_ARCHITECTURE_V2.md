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

只能：

Presentation -> Application -> Domain -> Infrastructure

禁止反向依赖。

## Core Runtime Flow

External Market
→ Provider Adapter
→ Market Domain
→ Chan Engine
→ Snapshot Publisher
→ API
→ TradingView
