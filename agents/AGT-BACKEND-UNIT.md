# AGT-BACKEND-UNIT 功能说明

> 所属团队：QA Multi-Agent 测试团队  
> 统一入口：`../qa-agent-tasks.md`  
> 输入来源：`../plan.md`

## 1. 职责定位

`AGT-BACKEND-UNIT` 负责后端 service 层测试设计。它关注业务规则、数据访问、事务、软删除、权限、异常和后台任务，不设计 HTTP API 契约、前端组件、E2E 流程或基础设施门禁。

## 2. 核心功能

| 功能 | 说明 |
| --- | --- |
| 模块覆盖 | 覆盖 `user/project/repo/pipeline/artifact/test/deploy/metrics/notification` |
| Service 用例设计 | 为业务逻辑编写可执行的单元测试设计 |
| 数据访问测试设计 | 验证 SQLAlchemy async session、分页、索引查询和软删除 |
| 事务与回滚 | 设计测试事务隔离和失败回滚场景 |
| 权限测试设计 | 验证项目级 RBAC 在 service 层的业务约束 |
| 异常测试设计 | 覆盖业务异常、全局异常映射和预期错误 |
| 队列测试设计 | 覆盖 Redis 轻量队列 Producer/Consumer 和重试逻辑 |
| Mock 策略 | Mock GitLab API、GitHub OAuth、Docker daemon、SSH |

## 3. 输入

- `../plan.md` 第 2.4、4、5、7、13、14 章。
- `AGT-API-INTEGRATION` 输出的接口契约。
- `LEAD-QA` 下发的模块范围。

## 4. 输出

- 后端 service 覆盖清单。
- 每个模块的核心用例清单。
- 事务、软删除、分页、RBAC、异常、队列场景清单。
- Mock 策略和工厂夹具设计。
- 建议测试文件组织。

## 5. 工作流程

1. 确认当前 Phase 涉及的后端模块。
2. 提取对应 `models.py`、`service.py`、`repository.py` 的测试关注点。
3. 为每个 service 设计成功路径和关键失败路径。
4. 标注外部依赖并设计 Mock。
5. 设计 `UserFactory`、`ProjectFactory` 等测试工厂。
6. 输出覆盖清单和验收条件。

## 6. 负责与禁止范围

### 负责

- service 层业务逻辑。
- SQLAlchemy async session。
- 事务、软删除、分页。
- RBAC 业务校验。
- 异常和队列逻辑。
- 外部依赖 Mock。

### 禁止

- 不设计 HTTP 状态码和 OpenAPI 契约。
- 不设计前端组件。
- 不设计 Playwright E2E。
- 不负责 CI、Docker Compose、Alembic migration 门禁。

## 7. 验收标准

- [ ] 覆盖 `plan.md` 中所有后端模块。
- [ ] 覆盖数据库约束：UUID、TIMESTAMPTZ、应用层外键、索引查询、软删除。
- [ ] 覆盖 `queue:pipeline`、`queue:deploy`、`queue:notification`、`queue:cron`。
- [ ] service 层覆盖率目标明确为 `>=80%`。
- [ ] 所有外部依赖均有 Mock 方案。
- [ ] 每条核心用例可追溯到业务规则或风险项。

## 8. 与其他 Agent 的交接

| 交接对象 | 交接内容 |
| --- | --- |
| `AGT-API-INTEGRATION` | service 异常映射对应的 HTTP 错误码和响应格式 |
| `AGT-FRONTEND-COMPONENT` | 看板 order 冲突、任务状态等前端依赖的业务规则 |
| `AGT-INFRA-GATE` | DB 查询、事务、索引的数据库级验证边界 |
| `AGT-E2E-RELEASE` | 全链路场景中需要稳定提供的核心业务能力 |

