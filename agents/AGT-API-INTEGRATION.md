# AGT-API-INTEGRATION 功能说明

> 所属团队：QA Multi-Agent 测试团队  
> 统一入口：`../qa-agent-tasks.md`  
> 输入来源：`../plan.md`

## 1. 职责定位

`AGT-API-INTEGRATION` 负责 REST/WebSocket API 契约测试设计。它为约 98 个端点设计成功路径、鉴权、RBAC、校验、错误码和外部依赖 Mock，不深入 service 内部实现。

## 2. 核心功能

| 功能 | 说明 |
| --- | --- |
| 端点矩阵 | 按模块整理全部 API 端点和测试状态 |
| 成功路径 | 每个端点至少设计 1 条成功路径 |
| 认证测试 | JWT、Refresh Token、登出、当前用户 |
| 权限测试 | 项目级 Owner/Member/Viewer RBAC |
| 校验测试 | Pydantic v2 请求校验和 422 场景 |
| 错误码测试 | 401、403、404、409、422、429、500 |
| 分页与软删除 | 列表分页和 `deleted_at` 过滤 |
| WebSocket 测试 | 流水线日志连接、心跳、取消、断开 |
| OpenAPI 校验 | 路由在 `/docs` 可见可交互，schema 正确 |

## 3. 输入

- `../plan.md` 第 4.3、7、13、14 章。
- `AGT-BACKEND-UNIT` 的 service 业务规则。
- `LEAD-QA` 下发的端点范围。

## 4. 输出

- API 端点测试矩阵。
- 请求、响应和校验失败用例清单。
- 认证与 RBAC 矩阵。
- 错误码覆盖表。
- Webhook 和 WebSocket 测试设计。
- 外部服务 Mock 接口约定。

## 5. 工作流程

1. 从 `plan.md` 第 4.3 章提取全部端点。
2. 按模块分类并分配测试优先级。
3. 为每个端点设计成功路径和关键失败路径。
4. 覆盖认证、RBAC、错误码、分页和软删除。
5. 对 Webhook、WebSocket 和限流单独设计场景。
6. 输出矩阵和验收清单。

## 6. 负责与禁止范围

### 负责

- API 路径和 HTTP 方法。
- 请求/响应 schema。
- 认证和授权。
- 错误码和限流。
- Webhook 和 WebSocket。

### 禁止

- 不设计 service 内部算法。
- 不设计数据库实现细节。
- 不设计 Vue 组件。
- 不设计 Playwright E2E。
- 不负责 CI、迁移和容器门禁。

## 7. 验收标准

- [ ] 覆盖所有 API 模块。
- [ ] 每个端点至少有 1 条成功路径。
- [ ] 覆盖 JWT、Refresh Token 和项目级 RBAC。
- [ ] 覆盖 401、403、404、409、422、429、500。
- [ ] 覆盖响应格式：`data`、`data + meta`、`error`。
- [ ] 覆盖 OpenAPI 3.1 可见性和 schema 校验。
- [ ] 不重复定义 service 内部实现。

## 8. 与其他 Agent 的交接

| 交接对象 | 交接内容 |
| --- | --- |
| `AGT-BACKEND-UNIT` | 需要 service 层提供的业务错误和状态规则 |
| `AGT-FRONTEND-COMPONENT` | 前端调用的接口错误和 token 刷新行为 |
| `AGT-E2E-RELEASE` | 全链路用户操作对应的 API 前置条件 |
| `AGT-INFRA-GATE` | OpenAPI 文档和限流配置的门禁验证 |

