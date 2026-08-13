# QA Multi-Agent 测试团队任务清单

> 输入文件：`./plan.md`  
> 当前阶段：测试设计与验收，不执行产品代码或测试代码  
> 运行规范：`./multica-team-spec.md`  
> 验收矩阵：`./qa-acceptance-matrix.md`  
> 更新时间：2026-08-13

## 1. 使用约定

本文件定义一个队长 Agent、一个代码评审 Agent 和 5 个测试 Agent。队长统一读取任务、调用 Agent、汇总结果，并对边界冲突和测试缺口做最终裁决。

QA 测试 Agent 当前只输出测试范围、用例清单、风险、夹具设计、验收标准和交接信息。`AGT-CODE-REVIEW` 在实现代码出现后评审 diff；仓库目前没有实现代码，因此不要求运行测试或编写测试代码。

## 2. 输入源映射

| `plan.md` 章节 | 主要内容 | 主要使用 Agent |
| --- | --- | --- |
| 一、项目定义与范围 | MVP 模块边界、暂不做能力 | `LEAD-QA` |
| 二、技术约束 | Python、FastAPI、Vue3、PostgreSQL、Redis、代码规范 | 所有 Agent |
| 三、系统架构总览 | Nginx、FastAPI、Worker、PostgreSQL、Redis | `AGT-INFRA-GATE`、`AGT-E2E-RELEASE` |
| 四、后端模块拆分 | 模块目录、约 98 个 API 端点 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` |
| 五、数据库设计 | schema、表、索引、状态、软删除 | `AGT-BACKEND-UNIT`、`AGT-INFRA-GATE` |
| 六、前端架构 | 路由、视图、组件、Store、API 封装 | `AGT-FRONTEND-COMPONENT` |
| 七、API 设计约定 | REST、响应格式、认证、错误码、限流 | `AGT-API-INTEGRATION` |
| 八、Docker Compose 部署 | 服务、healthcheck、启动流程 | `AGT-INFRA-GATE`、`AGT-E2E-RELEASE` |
| 九、分阶段开发计划 | Phase 0-4 | `LEAD-QA`、`AGT-E2E-RELEASE`、`AGT-INFRA-GATE` |
| 十、质量门禁 | API 文档、覆盖率、lint、migration、软删除 | `AGT-INFRA-GATE` |
| 十一、关键风险 | 表规模、流水线引擎、看板冲突、WebSocket 泄漏 | `LEAD-QA`、各专业 Agent |
| 十三、测试策略 | pytest、httpx、vitest、Playwright | 所有测试 Agent |
| 十四、后台任务队列 | Redis 队列、Worker、重试 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` |
| 十五、日志与监控 | JSON 日志、健康检查 | `AGT-INFRA-GATE` |
| 十六、CI/CD 配置 | ruff、mypy、pytest、pnpm lint/build | `AGT-INFRA-GATE` |

## 3. Agent 总览

| Agent ID | 名称 | 主测试层次 | 主边界 |
| --- | --- | --- | --- |
| `LEAD-QA` | 队长 | 调度、汇总、裁决 | 不负责单个模块的细节用例设计 |
| `AGT-CODE-REVIEW` | 代码评审 Agent | 实现 diff、标准、安全、测试性 | 只评审，不修改代码；不替代测试设计 |
| `AGT-BACKEND-UNIT` | 后端单元测试 Agent | service 层 | 不负责 API 契约、前端、E2E、基础设施 |
| `AGT-API-INTEGRATION` | API 集成测试 Agent | REST/WebSocket 接口 | 不负责 service 内部实现、前端、E2E |
| `AGT-FRONTEND-COMPONENT` | 前端组件测试 Agent | Vue3 组件、Store、交互 | 不负责后端测试、E2E、CI |
| `AGT-E2E-RELEASE` | 端到端与发布验收 Agent | 跨模块全链路 | 不负责单模块单元测试和 API 契约细节 |
| `AGT-INFRA-GATE` | 基础设施与质量门禁 Agent | CI、DB、迁移、容器、监控 | 不负责产品级测试用例设计 |

### 3.1 独立 Agent 文档

| Agent | 独立文档 |
| --- | --- |
| `LEAD-QA` | [agents/LEAD-QA.md](agents/LEAD-QA.md) |
| `AGT-CODE-REVIEW` | [agents/AGT-CODE-REVIEW.md](agents/AGT-CODE-REVIEW.md) |
| `AGT-BACKEND-UNIT` | [agents/AGT-BACKEND-UNIT.md](agents/AGT-BACKEND-UNIT.md) |
| `AGT-API-INTEGRATION` | [agents/AGT-API-INTEGRATION.md](agents/AGT-API-INTEGRATION.md) |
| `AGT-FRONTEND-COMPONENT` | [agents/AGT-FRONTEND-COMPONENT.md](agents/AGT-FRONTEND-COMPONENT.md) |
| `AGT-E2E-RELEASE` | [agents/AGT-E2E-RELEASE.md](agents/AGT-E2E-RELEASE.md) |
| `AGT-INFRA-GATE` | [agents/AGT-INFRA-GATE.md](agents/AGT-INFRA-GATE.md) |

### 3.2 作者与运行文档

| 文档 | 作用 |
| --- | --- |
| [agents/DEV-AUTHOR.md](agents/DEV-AUTHOR.md) | 定义对应模块作者 Agent 的修改和验证协议 |
| [multica-team-spec.md](multica-team-spec.md) | 定义状态机、消息、工件、权限、并发和升级规则 |
| [qa-acceptance-matrix.md](qa-acceptance-matrix.md) | 定义 Phase 0-4 主责、产出、退出条件和阻塞升级 |

## 4. LEAD-QA 队长任务

### 4.1 任务目标

从 `plan.md` 拆出测试范围，按本文件派发任务，合并结果，保证测试覆盖不重叠、不遗漏，并形成每个 Phase 的验收结论。

### 4.2 输入

- `./plan.md`
- 各 Agent 返回的测试设计结果
- 各 Agent 标记的跨边界问题

### 4.3 负责范围

- 生成测试任务包。
- 分配主 Agent 和交付物。
- 分发 `AGT-CODE-REVIEW` 评审任务，并把 `CHANGES_REQUESTED` 转交对应 `DEV-AUTHOR-{module}`。
- 检查每个 `plan.md` 测试约束是否已被覆盖。
- 检查模块、端点、阶段、测试层次之间的归属冲突。
- 汇总风险清单和 Phase 0-4 验收状态。
- 对 Agent 无法解决的边界冲突做最终裁决。

### 4.4 禁止范围

- 不直接编写某个模块的详细测试用例。
- 不直接修改测试代码或产品代码。
- 不替代任一专业 Agent 的执行。

### 4.5 输出物

- `qa-task-status.md` 或本文件中的状态表。
- 测试范围覆盖矩阵。
- 风险与缺口清单。
- Phase 0-4 验收结论。

### 4.6 验收标准

- 7 个 Agent 均有明确任务包和输出。
- 所有约 98 个端点、所有后端模块、所有关键前端路由和组件均有主归属。
- 每个跨边界问题都有裁决记录。
- 每个 Phase 的发布门禁都有 `通过/阻塞` 结论。

### 4.7 调用协议

队长向专业 Agent 下发任务包：

```json
{
  "task_id": "QA-TASK-001",
  "agent_id": "AGT-API-INTEGRATION",
  "source": "./plan.md",
  "scope": "user/project/repo/pipeline/artifact/test/deploy/metrics/notification API",
  "excluded_scope": "service internals, frontend, E2E, infra",
  "deliverable": "API endpoint test matrix and auth/RBAC cases",
  "due_gate": "Phase completion"
}
```

Agent 返回：

```json
{
  "task_id": "QA-TASK-001",
  "agent_id": "AGT-API-INTEGRATION",
  "status": "completed",
  "deliverables": ["api_matrix.md", "auth_rbac_matrix.md"],
  "handoffs": ["board conflict path to AGT-FRONTEND-COMPONENT"],
  "gaps": [],
  "risks": ["Webhook provider behavior not executable without credentials"]
}
```

## 5. AGT-BACKEND-UNIT 后端单元测试 Agent

### 5.1 任务目标

设计 `user/project/repo/pipeline/artifact/test/deploy/metrics/notification` 所有 service 层单元测试，确保核心业务逻辑可验证，后端 service 层覆盖率目标为 `>=80%`。

### 5.2 负责范围

- SQLAlchemy 2.0 async session 和事务边界。
- 软删除 `deleted_at` 过滤。
- 分页工具和列表查询。
- 项目级 RBAC 的业务校验。
- 全局异常映射。
- Redis 轻量队列的 Producer/Consumer 逻辑。
- Pipeline、Deploy、Notification、Cron 队列任务。
- Mock 外部依赖：GitLab API、GitHub OAuth、Docker daemon、SSH。
- 测试工厂：`UserFactory`、`ProjectFactory`、`PipelineFactory`、`DeployFactory` 等。

### 5.3 禁止范围

- 不设计 HTTP 状态码和 OpenAPI 契约测试。
- 不设计前端组件测试。
- 不设计 Playwright E2E 流程。
- 不负责 Docker Compose、CI、migration 等基础设施门禁。

### 5.4 输出物

- 后端 service 覆盖清单。
- 每个模块的核心用例清单。
- 事务、软删除、分页、RBAC、异常、队列场景清单。
- Mock 策略和工厂夹具设计。
- 建议测试文件组织。

### 5.5 验收标准

- 覆盖 `plan.md` 中所有后端模块的 service 层。
- 覆盖 `plan.md` 第 2.4 节数据库约束：UUID、TIMESTAMPTZ、应用层外键、索引查询、软删除。
- 覆盖 `plan.md` 第 14 节 4 个 Redis 队列。
- 所有外部依赖均有 Mock 方案。
- 每条核心用例可追溯到业务规则或风险项。

## 6. AGT-API-INTEGRATION API 集成测试 Agent

### 6.1 任务目标

为约 98 个 REST/WebSocket 端点设计 API 集成测试，保证每个端点至少有 1 条成功路径，并覆盖关键鉴权、错误和契约场景。

### 6.2 负责范围

| 模块 | 主要端点范围 |
| --- | --- |
| user | 注册、登录、刷新、登出、当前用户、团队、用户管理 |
| project | 项目、成员、迭代、需求、任务、Bug、看板 |
| repo | 仓库连接、分支、提交、Webhook |
| pipeline | 流水线 CRUD、触发、运行历史、取消、WebSocket 日志 |
| artifact | 仓库 CRUD、上传、列表 |
| test | 用例集、用例、测试计划、测试执行 CRUD |
| deploy | 环境、部署任务、凭证 CRUD |
| metrics | 吞吐、缺陷趋势、部署频率、交付周期 |
| notification | 消息、已读、规则 CRUD |

- JWT Bearer Token、Refresh Token、除 `/api/v1/auth/*` 外均需认证。
- 项目级 RBAC：Owner、Member、Viewer。
- 限流：单用户 100 req/min。
- 错误码映射：422、401、403、404、409、429、500。
- 响应格式：单条 `data`、分页 `data + meta`、错误 `error`。
- Pydantic v2 请求和响应 schema 校验。
- OpenAPI 3.1 路由可交互性验证。
- WebSocket 连接、心跳、取消和断开场景。

### 6.3 禁止范围

- 不设计 service 内部算法或数据库实现细节。
- 不设计 Vue 组件测试。
- 不设计 Playwright 全链路测试。
- 不负责 docker compose、CI、migration。

### 6.4 输出物

- API 端点测试矩阵。
- 请求/响应和校验失败用例清单。
- 认证与 RBAC 矩阵。
- 错误码覆盖表。
- Webhook 和 WebSocket 接口测试设计。
- 外部服务 Mock 接口约定。

### 6.5 验收标准

- 覆盖 `plan.md` 中所有 API 模块。
- 每个端点至少有 1 条成功路径。
- 覆盖 401、403、404、409、422、429、500 等关键错误。
- 覆盖分页、软删除过滤、幂等/冲突和 OpenAPI 校验。
- 不重复设计 service 内部逻辑，只通过接口契约引用。

## 7. AGT-FRONTEND-COMPONENT 前端组件测试 Agent

### 7.1 任务目标

设计 Vue3 + TypeScript + Naive UI 关键组件、页面、Store、Axios 拦截器和交互边界测试，保证前端关键组件有测试覆盖，并满足 ESLint、Prettier、TypeScript strict 要求。

### 7.2 负责范围

- 登录、注册。
- Dashboard。
- 项目列表、项目详情、看板。
- 需求、任务、Bug 列表和详情。
- 迭代时间线。
- 流水线列表、编辑、运行详情、LogViewer。
- 测试用例集、用例、测试计划、测试执行。
- 部署管理和历史。
- 用户管理和团队管理。
- Pinia Store：`auth`、`project`、`board`。
- Axios 拦截器：token 刷新、401 重试。
- 关键组件：`BoardColumn`、`BoardCard`、`ItemDetailDrawer`、`LogViewer`、`UserSelector`、`ConfirmDialog`、`MarkdownEditor`。

### 7.3 禁止范围

- 不编写后端测试。
- 不设计 Playwright 全流程 E2E。
- 不负责 CI、数据库迁移、Docker Compose 门禁。

### 7.4 输出物

- 关键路由和组件测试清单。
- Pinia Store 状态变化和异步调用测试点。
- Axios 拦截器和错误处理测试点。
- 看板拖拽、冲突回滚、乐观更新测试点。
- LogViewer 虚拟滚动、搜索、stdout/stderr 着色测试点。
- UserSelector 远程搜索和 300ms 防抖测试点。
- 空态、加载态、错误态和响应式布局检查点。

### 7.5 验收标准

- 覆盖 `plan.md` 第 6 节列出的关键路由和组件。
- 覆盖 `plan.md` 第 6.4 节关键组件接口。
- 覆盖看板拖拽冲突和 WebSocket 断连清理。
- 所有测试点对应 Vue3 Composition API 和 Naive UI 组件行为。
- 不越界编写后端或 E2E 用例。

## 8. AGT-E2E-RELEASE 端到端与发布验收 Agent

### 8.1 任务目标

设计 Playwright 端到端冒烟和回归场景，覆盖从登录到交付的跨模块用户路径，并形成发版前验收清单。

### 8.2 负责范围

- 登录 -> Dashboard -> 项目。
- 创建迭代、需求、任务、Bug，并在看板中流转。
- 创建并触发流水线，查看运行日志，取消运行。
- 创建测试用例集、测试计划并执行测试。
- 创建环境并触发部署。
- 查看效能度量和通知。
- `docker compose up` 后的健康检查和主要页面可访问性。
- 发布前回归场景和缺陷闭环场景。

### 8.3 禁止范围

- 不设计 service 层单元测试。
- 不逐条设计所有 API 的契约测试。
- 不深入 CI/DB/migration 内部实现。

### 8.4 输出物

- 端到端冒烟场景清单。
- 关键用户旅程脚本步骤。
- 回归场景清单。
- 发布前验收清单。
- E2E 环境准备和测试数据初始化方案。
- 跨模块依赖和外部服务替换方案。

### 8.5 验收标准

- 覆盖 Phase 0-4 的关键业务闭环。
- 覆盖健康检查、登录、项目、看板、流水线、测试、部署、度量和通知。
- 所有 E2E 场景不使用真实外部凭据。
- 每个场景都可追溯到 `plan.md` 的阶段或风险项。

## 9. AGT-INFRA-GATE 基础设施与质量门禁 Agent

### 9.1 任务目标

设计质量门禁、CI、数据库迁移、容器启动、日志和监控验证，确保每个 Phase 交付前满足 `plan.md` 第 10、15、16 章要求。

### 9.2 负责范围

- 后端 `ruff check`、`ruff format`、`mypy --strict`。
- 前端 `ESLint`、`Prettier`、`TypeScript strict`、`pnpm build`。
- `pytest --cov=backend/app` 覆盖率门禁。
- Alembic migration `upgrade` 和 `downgrade` 双向验证。
- PostgreSQL schema、索引、查询事务、软删除过滤。
- Docker Compose 服务启动和 healthcheck。
- Nginx `/api/*`、WebSocket、前端静态资源路由。
- Redis Session、限流和任务队列连通性。
- JSON 日志、`request_id`、`user_id`、`project_id` 字段。
- `GET /api/v1/health` 返回数据库和 Redis 状态。

### 9.3 禁止范围

- 不设计产品级业务测试用例。
- 不负责前端页面交互细节。
- 不负责 service 层算法逻辑测试。

### 9.4 输出物

- Phase 0-4 质量门禁检查表。
- CI 执行步骤和通过条件。
- Alembic migration 测试场景。
- Docker Compose 启动验收清单。
- 日志、限流、健康检查验证方案。
- 数据库索引和软删除验证清单。

### 9.5 验收标准

- 覆盖 `plan.md` 第 10 章全部质量门禁。
- 覆盖第 15 章日志级别和健康检查。
- 覆盖第 16 章 pre-commit 和 GitHub Actions 流程。
- 每个门禁都有可执行命令和通过/阻塞标准。

## 10. AGT-CODE-REVIEW 代码评审 Agent

### 10.1 任务目标

对实现代码 diff、测试代码变更和基础设施变更进行评审，确保代码符合 `plan.md` 的技术约束、安全要求、可测试性和质量门禁。评审不修改代码，发现的问题交回对应作者 Agent 修改和验证，然后重新评审。

### 10.2 负责范围

- 后端 Python/FastAPI/SQLAlchemy 代码。
- 前端 Vue3/TypeScript/Naive UI 代码。
- 数据库迁移、Docker Compose、CI/CD 配置。
- 测试代码和测试数据构造。
- 代码规范、安全和可测试性。

### 10.3 禁止范围

- 不直接修改产品代码或测试代码。
- 不替代 `AGT-BACKEND-UNIT` 设计 service 层测试。
- 不替代 `AGT-API-INTEGRATION` 设计 API 用例。
- 不替代 `AGT-INFRA-GATE` 执行 CI 或发布门禁。

### 10.4 评审闭环

`LEAD-QA` 将变更 diff 和对应作者映射发给 `AGT-CODE-REVIEW`，执行以下闭环：

```text
REVIEW -> APPROVED | CHANGES_REQUESTED
                     |
                     v
              DEV-AUTHOR-{module}
             修改 + 本地验证
                     |
                     v
              RE-REVIEW
```

每次评审结果必须包含：

- 严重级别：`critical`、`high`、`medium`、`low`。
- 文件路径和行号。
- 问题说明和修改建议。
- 作者需要执行的验证命令。
- 是否允许重新评审。

作者 Agent 返回：

- 已修改文件。
- 修改说明。
- 验证命令和执行结果。
- 需要复审的 diff。

同一变更最多进行 2 次 `CHANGES_REQUESTED` 复审。仍未通过时，转交 `LEAD-QA` 做阻塞裁决，不得直接合入。

### 10.5 输出物

- 代码评审报告。
- 严重问题清单。
- 作者 Agent 修改与验证记录。
- 复审通过或阻塞记录。

### 10.6 验收标准

- [ ] 所有进入 Phase 验收的代码 diff 均已评审。
- [ ] `critical`、`high` 问题已解决或由 `LEAD-QA` 明确接受。
- [ ] 作者 Agent 已运行 lint、type check、单测或构建验证。
- [ ] 复审通过后才有 `APPROVED` 状态。
- [ ] 未通过复审的变更不进入发布门禁。

## 11. 测试归属矩阵

### 11.1 模块归属

| 模块 | 主 Agent | 辅助 Agent |
| --- | --- | --- |
| user | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` |
| project | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` |
| repo | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-E2E-RELEASE` |
| pipeline | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` |
| artifact | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-E2E-RELEASE` |
| test | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` |
| deploy | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` |
| metrics | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT` |
| notification | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | `AGT-FRONTEND-COMPONENT`、`AGT-E2E-RELEASE` |

### 11.2 测试层次归属

| 测试层次 | 主 Agent |
| --- | --- |
| 后端单元测试 | `AGT-BACKEND-UNIT` |
| API 集成测试 | `AGT-API-INTEGRATION` |
| 前端组件测试 | `AGT-FRONTEND-COMPONENT` |
| E2E/发布验收 | `AGT-E2E-RELEASE` |
| 质量门禁与基础设施 | `AGT-INFRA-GATE` |
| 代码评审 | `AGT-CODE-REVIEW` |

### 11.3 阶段归属

| Phase | 主验收 Agent | 重点 |
| --- | --- | --- |
| Phase 0 | `AGT-INFRA-GATE` | 一键启动、healthcheck、空壳页面 |
| Phase 1 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | IAM、项目、需求、任务、Bug、看板 |
| Phase 2 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | 仓库、流水线、Worker、WebSocket |
| Phase 3 | `AGT-BACKEND-UNIT`、`AGT-API-INTEGRATION` | 测试管理、部署、制品 |
| Phase 4 | `AGT-E2E-RELEASE`、`AGT-INFRA-GATE` | 度量、通知、全链路回归 |

## 12. 交接与边界规则

### 12.1 主归属规则

- 每个测试关注点只有一个主 Agent。
- 辅助 Agent 只能消费主 Agent 的输出，不能重复定义主 Agent 的测试范围。
- 若发现边界冲突或缺口，Agent 必须标为 `handoff` 或 `gap` 返回给 `LEAD-QA`。

### 12.2 典型边界

| 关注点 | 主 Agent | 辅助 Agent 只负责 |
| --- | --- | --- |
| JWT、Refresh Token、RBAC | `AGT-API-INTEGRATION` | Backend 验证 service 校验；Frontend 验证 token 拦截器 |
| 看板拖拽冲突 | `AGT-FRONTEND-COMPONENT` | API 提供 409 冲突用例；Backend 提供 order 逻辑 |
| Pipeline Worker 与 Redis 队列 | `AGT-BACKEND-UNIT` | API 提供触发/取消接口；E2E 验证完整运行 |
| WebSocket 日志 | `AGT-API-INTEGRATION` | Frontend 验证 LogViewer；E2E 验证真实推送 |
| Docker Compose 与 CI | `AGT-INFRA-GATE` | E2E 只负责启动后关键用户路径 |
| 软删除与事务 | `AGT-BACKEND-UNIT` | Infra 负责 migration 和数据库级验证 |
| 实现 diff 与代码质量 | `AGT-CODE-REVIEW` | `DEV-AUTHOR-{module}` 修改并验证；QA Agent 不替代代码评审 |

### 12.3 队长裁决规则

- Agent 之间若对归属有争议，`LEAD-QA` 以“最小重复、最贴近系统边界”为原则裁决。
- 无法从 `plan.md` 判定的业务细节，标记为 `ASSUMPTION`，不阻断测试设计。
- 最终输出中不得存在无主测试项。

## 13. 最终验收清单

- [ ] 已创建 7 个 Agent 任务卡。
- [ ] 每个 Agent 都有输入、范围、禁止范围、输出物和验收标准。
- [ ] 所有约 98 个 API 端点均进入 `AGT-API-INTEGRATION` 矩阵。
- [ ] 所有后端模块均进入 `AGT-BACKEND-UNIT` service 覆盖清单。
- [ ] 所有关键前端路由和组件均进入 `AGT-FRONTEND-COMPONENT` 清单。
- [ ] Phase 0-4 均有质量门禁和 E2E 冒烟场景。
- [ ] 外部依赖 Mock 策略明确。
- [ ] 交接、冲突和缺口处理规则明确。
- [ ] 代码评审闭环覆盖 `REVIEW -> AUTHOR_FIX -> VERIFY -> RE-REVIEW`。
- [ ] 作者 Agent 验证记录和复审结果可追踪。
- [ ] `multica-team-spec.md` 已定义状态机、消息、工件、权限和升级规则。
- [ ] `qa-acceptance-matrix.md` 已覆盖每个 Phase 的主责、产出、退出条件和阻塞升级。
- [ ] `LEAD-QA` 可依据本文件直接派发和汇总任务。

## 14. 当前假设

- “mutlica”按 Multi-Agent 理解。
- “同一有队长调用”按一个队长 Agent 统一派发、汇总和裁决理解。
- 当前目录没有业务实现代码，因此 Agent 输出测试设计和验收清单，不运行测试。
- 本文件及其 `agents/` 子文档只补充 QA/评审职责，不修改 `plan.md`。
