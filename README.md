# DevOps 平台测试计划与 Multi-Agent 团队

本仓库用于存放“开源 DevOps 一体化平台”的技术规划、QA 测试团队任务、代码评审闭环和 multica 多 Agent 运行规范。

> 当前阶段：测试设计与验收规划，不包含产品实现代码或可运行的测试套件。

## 1. 项目背景

目标项目是一个面向中小团队的轻量级 DevOps 一体化平台，覆盖：

- 项目管理：需求、任务、Bug、迭代、看板。
- 代码管理：对接 GitLab、GitHub 等外部仓库。
- CI/CD：可视化流水线编排和执行。
- 制品管理：Docker 镜像和通用制品。
- 测试管理：用例集、测试用例、测试计划、测试执行。
- 环境管理：开发、测试、生产环境纳管与部署。
- 度量分析：研发效能看板。

技术栈约束：

- 后端：Python 3.11+、FastAPI、SQLAlchemy 2.0、PostgreSQL 15+、Redis 7+。
- 前端：Vue3、TypeScript、Naive UI、Vite、pnpm。
- 部署：Docker Compose、Nginx。
- 测试：pytest、httpx、vitest、Playwright。

## 2. 仓库内容

| 文件 | 说明 |
| --- | --- |
| `README.md` | 本说明文档 |
| `plan.md` | 开源 DevOps 一体化平台完整技术规划 |
| `qa-agent-tasks.md` | QA 多 Agent 团队总入口 |
| `qa-acceptance-matrix.md` | Phase 0-4 QA 验收矩阵 |
| `multica-team-spec.md` | multica 团队运行规范 |
| `agents/LEAD-QA.md` | 队长 Agent |
| `agents/AGT-CODE-REVIEW.md` | 代码评审 Agent |
| `agents/AGT-BACKEND-UNIT.md` | 后端单元测试 Agent |
| `agents/AGT-API-INTEGRATION.md` | API 集成测试 Agent |
| `agents/AGT-FRONTEND-COMPONENT.md` | 前端组件测试 Agent |
| `agents/AGT-E2E-RELEASE.md` | 端到端与发布验收 Agent |
| `agents/AGT-INFRA-GATE.md` | 基础设施与质量门禁 Agent |
| `agents/DEV-AUTHOR.md` | 模块作者 Agent 接口 |
| `artifacts/` | 统一结构化工件区，包含任务、评审、QA 设计、作者修复和阶段状态 |
| `backend/` | FastAPI、SQLAlchemy、Alembic 后端骨架 |
| `frontend/` | Vue3、Vite、Naive UI 前端骨架 |
| `docker-compose.yml` | 本地一键启动编排 |
| `docker/` | Nginx 反向代理配置 |
| `docs/phase1-tech-debt.md` | Phase 1 技术债登记 |

## 3. 文档阅读顺序

建议按以下顺序阅读：

1. `plan.md`：理解产品范围、技术约束、模块和阶段计划。
2. `qa-agent-tasks.md`：理解测试团队如何拆解和协作。
3. `qa-acceptance-matrix.md`：理解每个 Phase 的验收和退出条件。
4. `multica-team-spec.md`：理解 Agent 在运行时的状态、消息、工件和权限。
5. `agents/`：查看每个 Agent 的具体职责和边界。
6. `artifacts/`：查看结构化工件的目录约束和当前阶段状态。

## 4. Agent 团队总览

| Agent | 职责 | 主要边界 |
| --- | --- | --- |
| `LEAD-QA` | 调度、汇总、风险、验收裁决 | 不设计具体测试用例 |
| `AGT-CODE-REVIEW` | 评审代码 diff 和测试代码 | 只评审，不修改代码 |
| `AGT-BACKEND-UNIT` | 后端 service 层测试设计 | 不负责 API、前端、E2E、基础设施 |
| `AGT-API-INTEGRATION` | API 契约、鉴权、错误码测试 | 不深入 service 内部实现 |
| `AGT-FRONTEND-COMPONENT` | 前端组件、Store、交互测试 | 不负责后端、E2E、CI |
| `AGT-E2E-RELEASE` | 跨模块端到端和发布验收 | 不设计单元测试和 API 契约 |
| `AGT-INFRA-GATE` | CI、迁移、容器、日志、健康检查 | 不设计产品业务用例 |
| `DEV-AUTHOR-{module}` | 修改对应模块代码并验证 | 只修改自己模块 |

## 5. 核心流程

### 5.1 QA 测试流程

```text
LEAD-QA 拆解任务
    |
    +-- AGT-BACKEND-UNIT
    +-- AGT-API-INTEGRATION
    +-- AGT-FRONTEND-COMPONENT
    +-- AGT-E2E-RELEASE
    +-- AGT-INFRA-GATE
    |
    v
LEAD-QA 合并、查缺口、裁决
```

### 5.2 代码评审闭环

```text
AGT-CODE-REVIEW
    |
    +-- APPROVED -> verified
    |
    +-- CHANGES_REQUESTED
              |
              v
       DEV-AUTHOR-{module}
       修改代码 + 本地验证
              |
              v
       AGT-CODE-REVIEW 复审
```

规则：

- 评审结果必须包含严重级别、文件位置、问题说明、修改建议和验证命令。
- 作者 Agent 必须提供修改说明、验证命令和执行结果。
- 同一变更最多复审 2 次，仍不通过时升级给 `LEAD-QA`。

## 6. multica 运行规范

`multica-team-spec.md` 定义了运行团队需要的通用契约：

- Agent 清单和模块作者映射。
- 任务状态机。
- 任务、评审结果、作者返回消息格式。
- 工件目录和字段。
- 文件系统、代码仓库、外部服务权限。
- 工具权限。
- 并发、重试、退避和超时。
- 人工升级条件。
- 上下文注入和可观测性。

注意：如果 `multica` 是具体运行时，还需要把本规范映射到其官方 manifest、Tool API、沙箱和状态机格式。

## 7. 当前状态与限制

当前仓库是测试设计文档，不是可运行系统：

- 没有业务实现代码。
- 没有可运行的 pytest、vitest、Playwright 测试套件。
- 没有 `multica` 官方配置文件。
- 没有真实 GitLab、GitHub、Docker daemon、SSH 凭据。

因此，当前内容主要用于统一团队职责、测试边界和运行契约。

## 8. 后续扩展建议

### 8.1 开始实现后

将 `agents/` 中的测试设计转为实际测试代码：

- `AGT-BACKEND-UNIT` 输出转为 `backend/tests/modules/`。
- `AGT-API-INTEGRATION` 输出转为 API 集成测试。
- `AGT-FRONTEND-COMPONENT` 输出转为 `frontend/src/**/*.spec.ts`。
- `AGT-E2E-RELEASE` 输出转为 Playwright 场景。
- `AGT-INFRA-GATE` 输出转为 CI 配置和迁移验证。

### 8.2 接入 multica

如果 multica 有官方运行时，需要增加：

- Agent manifest。
- Tool 调用声明。
- 状态机和消息 schema。
- 沙箱和权限映射。
- 外部服务 Mock 配置。
- 人工审批接入。

## 9. 文件结构

```text
.
├── README.md
├── plan.md
├── qa-agent-tasks.md
├── qa-acceptance-matrix.md
├── multica-team-spec.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── scripts/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   └── Dockerfile
├── docker/
│   └── nginx/
│       └── default.conf
├── docs/
│   └── phase1-tech-debt.md
├── agents/
    ├── LEAD-QA.md
    ├── AGT-CODE-REVIEW.md
    ├── AGT-BACKEND-UNIT.md
    ├── AGT-API-INTEGRATION.md
    ├── AGT-FRONTEND-COMPONENT.md
    ├── AGT-E2E-RELEASE.md
    ├── AGT-INFRA-GATE.md
    └── DEV-AUTHOR.md
└── artifacts/
    ├── tasks/
    ├── reviews/
    ├── qa/
    ├── author/
    └── status/
        └── phase-status.json
```

## 10. 贡献方式

修改文档时遵循以下约定：

- 保持中文 Markdown。
- Agent 边界变化时同步更新 `qa-agent-tasks.md` 和对应 `agents/*.md`。
- 运行规则变化时更新 `multica-team-spec.md`。
- 不把真实凭据、Token 或密钥提交到仓库。
