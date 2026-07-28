# Chan Engine Architecture V1.0

## 1. 定位

Chan Engine 是核心领域计算模块，不依赖数据库、API、TradingView。

核心原则：

- chan.py 不重写，通过 Adapter 接入
- 领域模型统一
- 计算结果版本化
- confirmed/predictive 分离
- 支持增量计算

## 2. 架构

```
ChanEngineInterface
        |
ChanPyAdapter
        |
chan.py runtime
        |
Domain DTO
        |
Snapshot Publisher
```

## 3. 核心职责

负责：

- K线标准化
- 分型
- 笔
- 线段
- 中枢
- 买卖点

不负责：

- 数据库
- UI
- API
- 策略

## 4. 运行模式

### Full

用于：

- 初始化
- 修复
- 回归基准

### Step

用于：

- 实时推进
- 回测
- 增量更新

## 5. 状态模型

结构对象：

```
Predictive
    |
Confirmed
    |
Frozen
```

Confirmed对象禁止修改。

## 6. 增量原则

禁止每次重新计算全部历史。

采用：

checkpoint + 新增K线 + 安全锚点

## 7. 输出

Chan Engine 输出：

- Domain Objects
- Snapshot DTO
- Events

不直接输出前端格式。
