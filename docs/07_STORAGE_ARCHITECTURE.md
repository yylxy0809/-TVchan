# Storage Architecture V1.0

## 1. 数据存储原则

系统采用职责分离。

## 2. Market Storage

free-stockdb 负责：

- Tick
- Bar
- 历史行情
- 实时行情

不保存：

- Chan状态
- 策略结果
- 发布版本

## 3. Application Storage

保存：

```
chan_runs
chan_snapshots
published_head
projection_snapshots
lifecycle_events
strategy_results
backtest_runs
```

## 4. Snapshot原则

计算结果必须：

- 可追踪
- 可复现
- 有版本
- 可回滚

## 5. 数据流

```
Market Data
 -> Snapshot
 -> Chan Compute
 -> Publish
 -> API
 -> Frontend
```
