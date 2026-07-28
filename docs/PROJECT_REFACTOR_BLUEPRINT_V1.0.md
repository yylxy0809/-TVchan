# 项目重构蓝图 V1.0

> Chan Theory Quantitative Platform 架构升级方案

## 1. 重构目标

将当前可运行的缠论 TradingView 系统，从功能驱动工程升级为长期可维护、可扩展的平台架构。

核心原则：

- 模块化
- 面向对象
- 高内聚低耦合
- 接口优先
- 事件驱动
- Adapter 隔离第三方
- 渐进式重构，不推倒重建

## 2. 总体架构

采用六层架构：

```
Presentation Layer
        |
Application Layer
        |
Domain Layer
        |
Infrastructure Layer
        |
Adapter Layer
        |
External Systems
```

## 3. 新目录结构

```
project/
├── apps/
│   ├── api/
│   └── frontend/
├── domain/
│   ├── market/
│   ├── chan/
│   ├── strategy/
│   └── signal/
├── application/
│   ├── services/
│   └── commands/
├── infrastructure/
│   ├── database/
│   ├── repository/
│   └── storage/
├── adapters/
│   ├── market/
│   ├── tradingview/
│   └── ai/
├── events/
├── tests/
└── docs/
```

## 4. 模块边界

### Market Domain
负责行情领域模型，不依赖数据库。

### Chan Domain
负责缠论结构计算，通过 Adapter 包装 chan.py。

### Snapshot Domain
负责计算结果版本、发布和一致性。

### Strategy Domain
负责策略、回测和交易逻辑。

### Presentation
只负责展示，不触发计算。

## 5. 核心接口设计

### MarketDataGateway

```python
get_bars()
get_latest_bar()
health_check()
```

### ChanEngineInterface

```python
compute()
step()
get_snapshot()
```

### ChartAdapter

```python
render_overlay()
update_objects()
```

## 6. 核心数据模型

统一领域模型：

- Bar
- MergedBar
- Fractal
- Stroke
- Segment
- Center
- Signal
- Snapshot

禁止重复定义。

## 7. Event设计

标准事件：

```
MarketBarUpdated
BarClosed
FractalGenerated
StrokeUpdated
StrokeConfirmed
SnapshotPublished
SignalGenerated
OverlayUpdated
```

模块通过事件通信，禁止跨模块调用内部实现。

## 8. 当前代码迁移计划

Phase 1:

建立 domain/application/infrastructure/adapter 分层。

Phase 2:

将 stockdb、TradingView、chan.py 接入 Adapter。

Phase 3:

引入 Event Bus，替换直接调用。

Phase 4:

完善 Snapshot、Version、Publish Head。

Phase 5:

建设 Strategy Engine 与 AI Module。

## 9. ADR列表

### ADR-001
不重写 chan.py，采用 Adapter。

### ADR-002
free-stockdb 只作为行情底座，不保存业务状态。

### ADR-003
TradingView 只负责展示，不负责计算。

### ADR-004
前端不可触发缠论计算。

### ADR-005
生命周期系统与主图展示解耦。

---

Version: 1.0.0
