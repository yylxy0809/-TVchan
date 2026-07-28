# Error Handling And Observability V1.0

## 1. 异常分层

```
DomainException
ApplicationException
InfrastructureException
AdapterException
ValidationException
```

## 2. 原则

- 明确失败
- 禁止静默错误
- 统一日志
- 可恢复异常自动重试

## 3. 健康检查

统一提供：

```
liveness
readiness
dependency health
```

## 4. 日志

记录：

- request id
- run id
- snapshot id
- version
- error context

## 5. 监控对象

- 数据源状态
- Chan计算状态
- 发布状态
- API状态
- 前端连接状态
