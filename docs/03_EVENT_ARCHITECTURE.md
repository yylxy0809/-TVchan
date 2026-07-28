# Event Architecture

## Goal

通过事件实现模块解耦。

## Event Flow

```
MarketBarUpdated
      |
      v
ChanCalculationRequested
      |
      v
ChanStructureUpdated
      |
      v
SnapshotPublished
      |
      v
OverlayUpdated
```

## Standard Events

- MarketBarUpdated
- BarClosed
- FractalGenerated
- StrokeConfirmed
- SegmentConfirmed
- CenterCreated
- SignalGenerated
- SnapshotPublished

## Rules

模块只能：

发布事件
监听事件

禁止：

调用其他模块内部方法。

## Future Usage

事件消费者：

- TradingView
- Strategy Engine
- AI Analyzer
- Backtest Engine
- Monitoring System
