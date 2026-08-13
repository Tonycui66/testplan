# QA 验收矩阵

> 配套：`qa-agent-tasks.md`、`multica-team-spec.md`、`agents/`  
> 作用：把 Phase 0-4 的 QA 产出、Agent 主责、质量门禁和退出条件落到可检查的矩阵。

## 1. 使用方式

`LEAD-QA` 在每个 Phase 开始前，按本矩阵确定参与 Agent、交付物和退出条件。Phase 结束时，只有矩阵中对应 `退出条件` 全部满足，才允许进入代码评审闭环或发布门禁。

## 2. Phase 验收矩阵

| Phase | 交付范围 | 主责 Agent | 参与 Agent | 必须产出 | 退出条件 |
| --- | --- | --- | --- | --- | --- |
| Phase 0 | 一键启动的空壳 | `AGT-INFRA-GATE` | `AGT-E2E-RELEASE` | Docker Compose 启动清单、healthcheck 验证、登录/Dashboard 冒烟 | `docker compose up` 成功，`GET /api/v1/health` 返回数据库和 Redis 正常 |
| Phase 1 | IAM + 项目管理 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` | IAM/项目 service 覆盖清单、API 端点矩阵、前端组件测试设计、E2E 冒烟 | 后端 service 覆盖设计完整，关键 API 成功路径全覆盖，关键前端组件有测试设计 |
| Phase 2 | CI/CD + 仓库对接 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` | 流水线/仓库 service 测试设计、API 矩阵、LogViewer/编辑器测试设计、E2E 闭环 | Worker/Redis 队列和 WebSocket 测试场景完整，外部仓库与 Docker 均 Mock |
| Phase 3 | 测试管理 + 部署 + 制品 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` | test/deploy/artifact 测试设计、API 矩阵、前端测试设计、E2E 闭环 | 测试用例/计划/执行、SSH 部署、制品上传均有成功路径和失败路径 |
| Phase 4 | 度量 + 通知 + 发布 | `AGT-E2E-RELEASE`、`AGT-INFRA-GATE` | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION`、`AGT-FRONTEND-COMPONENT` | 全链路回归清单、度量/通知测试设计、发布门禁、文档 | 发版冒烟覆盖全链路，所有 Phase 门禁汇总通过，无未裁决阻塞项 |

## 3. 全阶段通用门禁

以下门禁每个 Phase 都必须验证：

| 门禁 | 主责 Agent | 通过标准 |
| --- | --- | --- |
| API schema | `AGT-API-INTEGRATION` | 所有新增/变更 API 有 Pydantic schema |
| OpenAPI 可见性 | `AGT-API-INTEGRATION` | 路由在 `/docs` 可见可交互 |
| 后端测试设计 | `AGT-BACKEND-UNIT` | service 层覆盖设计达到 `>=80%` 目标 |
| 前端质量 | `AGT-FRONTEND-COMPONENT` | 关键组件有测试设计，TypeScript strict 无设计级缺口 |
| 代码评审 | `AGT-CODE-REVIEW` | 实现 diff 已评审，无未解决的 `critical`/`high` |
| 作者验证 | `DEV-AUTHOR-{module}` | lint、type check、单测或构建验证结果可追踪 |
| 迁移 | `AGT-INFRA-GATE` | Alembic `upgrade`/`downgrade` 双向可验证 |
| 容器 | `AGT-INFRA-GATE` | Docker Compose 服务和 healthcheck 验证通过 |
| 软删除 | `AGT-BACKEND-UNIT`、`AGT-INFRA-GATE` | 所有软删除资源查询正确过滤 |
| 分页 | `AGT-API-INTEGRATION` | 所有列表接口有分页测试设计 |
| 外部依赖 Mock | 对应专业 Agent | GitLab、GitHub、Docker daemon、SSH 均有 Mock 方案 |
| 日志 | `AGT-INFRA-GATE` | JSON 日志字段、健康检查、请求入口/出口有验证设计 |

## 4. 评审闭环矩阵

| 阶段 | 状态 | 主责 | 允许下一步 |
| --- | --- | --- | --- |
| 代码提交 | `pending_review` | `DEV-AUTHOR-{module}` | `AGT-CODE-REVIEW` |
| 评审中 | `reviewing` | `AGT-CODE-REVIEW` | `approved` 或 `changes_requested` |
| 要求修改 | `changes_requested` | `DEV-AUTHOR-{module}` | `verified` 后复审 |
| 作者验证 | `verified` | `DEV-AUTHOR-{module}` | `AGT-CODE-REVIEW` |
| 复审通过 | `approved` | `AGT-CODE-REVIEW` | `AGT-INFRA-GATE` 或 Phase 验收 |
| 复审阻塞 | `blocked` | `LEAD-QA` | 人工评审或拆分任务 |

## 5. 阻塞升级矩阵

| 场景 | 处理 |
| --- | --- |
| `critical` 安全问题 | 立即转 `LEAD-QA`，不进入发布 |
| 数据库 migration 无法安全回滚 | 转 `AGT-INFRA-GATE` 和 `LEAD-QA` |
| 外部凭据或密钥相关变更 | 禁止提交，转 `LEAD-QA` 人工处理 |
| 生产部署配置变更 | 转 `LEAD-QA`，确认后才允许进入门禁 |
| 同一变更复审 2 次仍不通过 | 转 `LEAD-QA` 做阻塞裁决 |
| Agent 边界归属冲突 | `LEAD-QA` 按系统边界和最小重复原则裁决 |

## 6. 验收检查表

- [ ] 每个 Phase 都有主责 Agent 和参与 Agent。
- [ ] 每个 Phase 都有必须产出。
- [ ] 每个 Phase 都有可检查的退出条件。
- [ ] 所有通用门禁映射到明确 Agent。
- [ ] 代码评审闭环状态完整。
- [ ] 阻塞升级条件完整。
- [ ] 没有无主测试项。
- [ ] `LEAD-QA` 可依据本矩阵直接验收。
