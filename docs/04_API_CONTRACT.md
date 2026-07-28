# API Contract

## Principle

API 是模块边界，不暴露内部实现。

## Market API

GET /market/bars

返回统一 Bar DTO。

GET /market/head

返回最新数据版本。

## Chan API

GET /chan/view

读取已发布结构。

禁止：

请求时触发计算。

## Snapshot API

GET /snapshot/head

返回当前发布版本。

## Contract Rules

- DTO 稳定
- 版本化
- 向后兼容
- 错误统一处理
