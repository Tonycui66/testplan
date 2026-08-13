# AGT-INFRA-GATE 功能说明

> 所属团队：QA Multi-Agent 测试团队  
> 统一入口：`../qa-agent-tasks.md`  
> 输入来源：`../plan.md`

## 1. 职责定位

`AGT-INFRA-GATE` 负责质量门禁、CI、数据库迁移、容器启动、日志和监控验证。它保证每个 Phase 交付前满足 `plan.md` 第 10、15、16 章要求，不设计产品业务测试用例。

## 2. 核心功能

| 功能 | 说明 |
| --- | --- |
| 后端质量 | `ruff check`、`ruff format`、`mypy --strict` |
| 前端质量 | ESLint、Prettier、TypeScript strict、`pnpm build` |
| 测试门禁 | `pytest --cov=backend/app` 和覆盖率阈值 |
| 数据库迁移 | Alembic `upgrade` 与 `downgrade` 双向验证 |
| 数据库约束 | schema、索引、事务、软删除过滤 |
| 容器启动 | Docker Compose 服务和 healthcheck |
| Nginx 路由 | `/api/*`、WebSocket、前端静态资源 |
| Redis | Session、限流、任务队列连通性 |
| 日志与监控 | JSON 日志、`request_id`、`user_id`、`project_id` |
| 健康检查 | `GET /api/v1/health` 返回数据库和 Redis 状态 |

## 3. 输入

- `../plan.md` 第 8、10、15、16 章。
- `AGT-BACKEND-UNIT` 的事务和数据库测试设计。
- `AGT-API-INTEGRATION` 的 OpenAPI 和限流契约。
- `AGT-FRONTEND-COMPONENT` 的 lint 和 strict 测试点。
- `LEAD-QA` 下发的 Phase 门禁范围。

## 4. 输出

- Phase 0-4 质量门禁检查表。
- CI 执行步骤和通过条件。
- Alembic migration 测试场景。
- Docker Compose 启动验收清单。
- 日志、限流、健康检查验证方案。
- 数据库索引和软删除验证清单。

## 5. 工作流程

1. 从 Phase 0-4 提取质量门禁。
2. 将门禁映射到可执行命令和通过条件。
3. 设计 Alembic migration 双向验证。
4. 设计 Docker Compose 启动、healthcheck 和 Nginx 路由验证。
5. 设计日志、限流、Redis、健康检查验证。
6. 输出 Phase 验收检查表。

## 6. 负责与禁止范围

### 负责

- CI 和质量门禁。
- 数据库迁移和数据库级验证。
- 容器和网络路由。
- 日志、限流、健康检查。

### 禁止

- 不设计产品级业务测试用例。
- 不设计前端页面交互细节。
- 不设计 service 层算法逻辑测试。

## 7. 验收标准

- [ ] 覆盖 `plan.md` 第 10 章全部质量门禁。
- [ ] 覆盖第 15 章日志级别和健康检查。
- [ ] 覆盖第 16 章 pre-commit 和 GitHub Actions。
- [ ] 每个门禁都有可执行命令和通过/阻塞标准。
- [ ] migration 支持 `upgrade` 和 `downgrade`。
- [ ] Docker Compose 服务依赖和 healthcheck 有验证方案。

## 8. 与其他 Agent 的交接

| 交接对象 | 交接内容 |
| --- | --- |
| `AGT-BACKEND-UNIT` | 数据库查询、事务、软删除的数据库级验证 |
| `AGT-API-INTEGRATION` | OpenAPI 文档和限流门禁 |
| `AGT-FRONTEND-COMPONENT` | ESLint、Prettier、TypeScript strict 门禁 |
| `AGT-E2E-RELEASE` | 发布前环境启动和健康检查结果 |
