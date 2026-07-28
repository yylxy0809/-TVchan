# Domain Model V2

## Principle

整个系统只能存在唯一领域模型。

## Market Models

### Bar

标准K线。

Fields:
- timestamp
- open
- high
- low
- close
- volume
- adjustment

## Chan Models

### Fractal

顶底分型。

### Stroke

笔。

状态：
- Candidate
- Confirmed
- Retracted

### Segment

线段。

### Center

中枢。

### Signal

买卖点和策略信号。

## Snapshot Models

### ChanSnapshot

记录一次计算结果。

包含：
- version
- inputVersion
- configVersion
- structures

### PublishedHead

当前发布版本。

## Rules

- 禁止模块重新定义类似对象
- confirmed 数据不可修改
- predictive 数据允许演化
- 所有对象必须支持稳定身份标识
