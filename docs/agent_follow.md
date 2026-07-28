# Agent Follow - TVchan 重构项目接手说明

> 本文件用于后续 AI Agent / 开发者接管项目。它记录项目背景、已完成决策、架构原则、当前状态和未来实施路线。

## 1. 项目背景

目标：构建一个缠论量化 + TradingView 可视化 + K线数据库的平台。

最终链路：

```
free-stockdb(K线数据)
        ↓
Market Data Adapter
        ↓
chan.py(缠论计算核心)
        ↓
Snapshot / Publication
        ↓
API
        ↓
TradingView只读主图
```

长期目标：

- 多周期缠论结构
- 实时增量计算
- 生命周期分析
- 逐K回放
- 选股
- 策略研究
- 回测平台

当前重构目标不是快速增加功能，而是建立可长期维护的软件工程基础。

---

# 2. 旧项目与新项目关系

## 旧项目

```
D:\TV
GitHub: yylxy0809/tv
```

用途：

- 功能验证来源
- 行为基线
- 测试和黄金数据参考

禁止：

- 不在旧项目继续架构重构
- 不整体复制旧代码
- 不直接迁移目录

## 新项目

```
D:\TVchan
GitHub: yylxy0809/-TVchan
```

用途：

未来正式产品代码。

原则：

> 按新架构重新建设，再逐项迁移旧能力。

---

# 3. 已完成架构设计

已建立：

```
docs/
├── SYSTEM_ARCHITECTURE
├── DOMAIN_MODEL
├── EVENT_ARCHITECTURE
├── API_CONTRACT
├── MIGRATION_PLAN
├── CHAN_ENGINE_ARCHITECTURE
├── STORAGE_ARCHITECTURE
├── ERROR_HANDLING
├── AI_AGENT_GUIDE
└── ADR
```

核心原则：

- Domain 不依赖框架
- Application 编排业务流程
- Infrastructure 提供技术实现
- Adapter 隔离第三方系统
- Presentation 只负责展示

---

# 4. 当前代码状态

## Wave 0 已完成

PR #3:

```
feat: bootstrap Wave 0 backend skeleton
```

包含：

- Python package边界
- FastAPI composition root
- /health接口
- pytest
- ruff
- mypy
- dependency boundary check
- CI

禁止包含：

- StockDB
- chan.py
- TradingView
- strategy
- replay
- lifecycle

---

# 5. 目标目录设计

建议结构：

```
backend/
└── src/tvchan/
    ├── domain/
    │   ├── market/
    │   │   └── bar.py
    │   ├── chan/
    │   ├── publication/
    │   └── signal/
    │
    ├── application/
    │   ├── services/
    │   ├── commands/
    │   └── ports/
    │
    ├── infrastructure/
    │   ├── storage
    │   ├── logging
    │   └── config
    │
    ├── adapters/
    │   ├── stockdb
    │   ├── chanpy
    │   └── tradingview
    │
    └── bootstrap/
        └── api.py
```

---

# 6. 核心接口设计

## MarketDataGateway

职责：行情读取。

接口：

```python
get_bars(symbol, timeframe, start, end)
get_security(symbol)
health()
```

禁止：

Domain直接调用StockDB。

---

## ChanEnginePort

职责：缠论计算抽象。

接口：

```python
compute(snapshot)
update(delta)
```

实现：

```
ChanEnginePort
        |
ChanPyAdapter
        |
chan.py
```

禁止重写chan.py核心算法。

---

## SnapshotService

职责：生成稳定计算快照。

包含：

- 输入数据
- 配置
- quality状态
- 计算版本

---

## PublicationService

职责：发布给前端的数据。

输出：

```
ChanSnapshot
PublishedHead
Projection
```

---

# 7. 数据模型规划

核心对象：

```
Bar
Fractal
Stroke
Center
Signal
ChanSnapshot
PublishedHead
```

规则：

- Domain对象不可依赖数据库
- Snapshot不可随意修改
- Published对象只读

---

# 8. 缠论设计原则

当前正式口径：

```
bi_fx_check=half
bi_allow_sub_peak=false
```

不要重新讨论严格笔。

生产主图：

只显示：

- 笔
- 中枢
- 买卖点

不显示：

- 线段
- 生命周期层
- 历史回放层

---

# 9. Wave路线

## Wave 0

已完成：工程边界。

## Wave 1

只做市场数据契约：

```
Canonical Bar
        ↓
MarketDataGateway
        ↓
StockDB Adapter
        ↓
Quality Policy
        ↓
Health/Readiness
```

不要进入Chan。

## Wave 2

Chan接入：

```
ChanEnginePort
        ↓
ChanPyAdapter
        ↓
Golden comparison
```

## Wave 3

发布体系：

```
Snapshot
Checkpoint
PublishedHead
Read API
```

## Wave 4

TradingView：

- Datafeed
- Overlay
- Browser acceptance

## Wave 5

高级能力：

- realtime
- lifecycle
- replay
- strategy
- backtest

---

# 10. Agent开发纪律

任何Agent必须：

1. 先读PROJECT.md和docs。
2. 不复制旧项目。
3. 不跨层调用。
4. 不创建无意义抽象。
5. 所有修改必须可测试。
6. 保持Git分支隔离。
7. 不修改外部chan.py源码。

---

# 11. 当前下一步

推荐顺序：

1. 合并Wave0 PR。
2. 合并Legacy Audit PR。
3. 创建Wave1 issue。
4. 实现Market Contract。
5. 通过测试后再进入Chan。

核心思想：

> 先建立稳定的软件系统，再迁移缠论能力；不要把旧项目的偶然实现复制成为未来债务。
