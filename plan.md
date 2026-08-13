# 开源 DevOps 一体化平台 — 完整技术规划

> 定位：类似华为 CIE（Cloud Intelligence Engine）+ 禅道的轻量级开源替代，面向中小团队的研发管理 + CI/CD 一体化平台。
> 更新时间：2026-08-03

---

## 一、项目定义与范围

### 1.1 核心定位

一个 **研发管理 + 持续交付** 一体化平台，覆盖从需求到上线的全流程：

- **项目管理**（禅道类能力）：需求/任务/Bug/迭代/看板
- **代码管理**：Git 仓库托管或对接外部仓库（GitHub/GitLab/Gitee）
- **CI/CD 流水线**：可视化流水线编排 + 执行引擎
- **制品管理**：Docker 镜像 / 通用制品仓库
- **测试管理**：用例管理 + 测试计划 + 缺陷追踪
- **环境管理**：开发/测试/生产环境纳管与部署
- **度量分析**：研发效能看板

### 1.2 MVP 范围约束

MVP 只做 **禅道（项目管理核心）+ CIE（流水线最小闭环）** 的交集最核心能力：

| 模块 | MVP 范围 | 暂不做 |
|------|---------|--------|
| 项目管理 | 项目/需求/任务/迭代/看板 CRUD | 工时、甘特图、自定义字段、高级报表 |
| 代码仓库 | 对接 GitLab/GitHub OAuth | 自建 Git 托管 |
| CI/CD | 单 stage 流水线（Shell 脚本执行） | 多 stage 并行、模板、触发器、缓存 |
| 制品 | Docker 镜像拉取/推送代理 | 制品版本管理、扫描 |
| 测试 | 用例与测试单管理 | 自动化测试对接 |
| 部署 | 单环境 SSH 部署任务 | 环境拓扑、审批流 |
| 权限 | 项目级 RBAC（Owner/Member/Viewer） | 细粒度资源权限 |

---

## 二、技术约束（硬性）

### 2.1 语言与框架约束

| 层次 | 选型 | 版本 | 约束说明 |
|------|------|------|---------|
| 后端语言 | Python | ≥3.11 | 类型注解全覆盖，mypy strict 模式 |
| 后端框架 | FastAPI | latest stable | RESTful 风格，Pydantic v2 做请求/响应模型 |
| ORM | SQLAlchemy 2.0 | async 模式 | 禁止手写 SQL 拼接，迁移用 Alembic |
| 数据库 | PostgreSQL | ≥15 | 单实例部署，按 schema 分隔模块 |
| 缓存/队列 | Redis | ≥7 | 用于 Session、限流、轻量任务队列 |
| 前端框架 | Vue3 + TypeScript | latest | Composition API + `<script setup>` |
| UI 组件库 | Naive UI | latest | 统一使用，禁止混用其他组件库 |
| 前端构建 | Vite | latest | pnpm 包管理 |
| 容器化 | Docker Compose | v2 | 仅 docker compose，不用 K8s |
| 反向代理 | Nginx | latest alpine | 统一入口 |

### 2.2 代码规范硬约束

- **后端**：ruff 格式化 + lint，pre-commit hook 强制
- **前端**：ESLint + Prettier + TypeScript strict
- **测试覆盖率**：后端核心 service 层 ≥80%，前端关键组件有测试
- **Git 提交**：Conventional Commits（`feat:` / `fix:` / `chore:` 等）
- **API 文档**：OpenAPI 3.1 自动生成，禁止手写

### 2.3 架构硬约束

1. **微服务拆分但共享数据库**：按模块拆服务，但 MVP 阶段共享一个 PostgreSQL（通过 schema 隔离），降低运维复杂度
2. **前后端分离**：Nginx 统一入口，`/api/*` 代理到 FastAPI，其他代理到前端静态资源
3. **无状态服务**：所有后端服务无状态，Session 存 Redis
4. **同步 HTTP + 异步任务**：即时操作走 REST，长任务（流水线执行）走后台任务队列
5. **禁止引入消息队列（MVP 阶段）**：用 Redis 做轻量任务队列，后期再换 RabbitMQ/Kafka

### 2.4 数据库设计约束

- 所有 ID 使用 UUID v4，禁止自增整数
- 所有时间戳使用 `TIMESTAMPTZ`
- 禁止数据库级外键约束（性能原因），外键关系通过应用层维护，但文档中标注逻辑外键
- 所有查询必须走索引，禁止全表扫描（EXPLAIN 验证）
- 软删除统一用 `deleted_at` 字段，查询时全局过滤 `WHERE deleted_at IS NULL`

### 2.5 Python 依赖约束

```
# requirements.txt 固定依赖
fastapi>=0.115,<1.0
uvicorn[standard]>=0.32,<1.0
sqlalchemy[asyncio]>=2.0,<3.0
asyncpg>=0.30,<1.0
alembic>=1.14,<2.0
pydantic>=2.10,<3.0
pydantic-settings>=2.7,<3.0
python-jose[cryptography]>=3.3,<4.0
passlib[bcrypt]>=1.7,<2.0
redis>=5.2,<6.0
httpx>=0.28,<1.0
python-multipart>=0.0.18,<1.0
websockets>=14.0,<15.0
```

---

## 三、系统架构总览

```
                          ┌─────────────┐
                          │   Browser   │
                          └──────┬──────┘
                                 │ HTTPS
                          ┌──────▼──────┐
                          │   Nginx     │  反向代理 + 静态资源
                          └──┬──────┬───┘
                    /api/*   │      │   / (静态)
              ┌──────────────▼─┐  ┌─▼─────────────┐
              │  FastAPI       │  │  Vue3 SPA      │
              │  (微服务网关)   │  │  (dist 静态)   │
              └──────┬─────────┘  └───────────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
  ┌────▼────┐  ┌─────▼──────┐  ┌──▼───────┐
  │Project  │  │  Pipeline  │  │  Deploy  │  微服务模块
  │Service  │  │  Service   │  │  Service │  (共享 DB)
  └────┬────┘  └─────┬──────┘  └──┬───────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
              ┌──────▼──────┐
              │ PostgreSQL  │  schema 隔离
              │ (project/   │
              │  pipeline/  │
              │  deploy/    │
              │  test/      │
              │  repo/)     │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │   Redis     │  Session / 限流 / 轻量队列
              └─────────────┘
```

### 3.1 组件清单

| 组件 | 容器名 | 端口 | 用途 |
|------|--------|------|------|
| Nginx | `nginx` | 80 | 反向代理 + 前端静态资源 + WebSocket 代理 |
| FastAPI 主服务 | `api` | 8000 | 统一的 API 网关，路由到各模块 Router |
| Worker | `worker` | — | 后台任务执行（流水线、部署），同镜像不同启动命令 |
| PostgreSQL | `postgres` | 5432 | 唯一关系数据库 |
| Redis | `redis` | 6379 | 缓存 + Session + 任务队列（RPUSH/BLPOP） |

### 3.2 单 FastAPI 进程的理由

- 前期团队小、请求量低，拆进程增加运维和调试成本
- 代码层面按 `app/modules/{project,pipeline,deploy,test,repo,user}/` 拆 Router，边界清晰
- 当某个模块需要独立扩缩容时，将该模块的 Router 拆到独立 FastAPI 进程即可

---

## 四、后端模块拆分

### 4.1 目录结构

```
backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI 应用入口
│   ├── config.py             # 配置中心（pydantic-settings）
│   ├── dependencies.py       # 公共依赖注入（DB Session、当前用户）
│   ├── models/
│   │   └── base.py           # SQLAlchemy Base + UUIDMixin + TimestampMixin
│   ├── core/
│   │   ├── security.py       # JWT + 密码哈希
│   │   ├── exceptions.py     # 全局异常处理
│   │   ├── redis_client.py   # Redis 连接池 + 队列操作
│   │   ├── pagination.py     # 分页工具
│   │   └── logging_config.py # 结构化日志配置
│   ├── middleware/
│   │   ├── cors.py
│   │   ├── request_id.py
│   │   └── rate_limit.py
│   └── modules/
│       ├── user/
│       ├── project/
│       ├── repo/
│       ├── pipeline/
│       ├── artifact/
│       ├── test/
│       ├── deploy/
│       ├── metrics/
│       └── notification/
├── tests/
│   ├── conftest.py
│   └── modules/
├── scripts/
│   ├── init_db.py
│   └── seed_data.py
├── Dockerfile
├── pyproject.toml
├── ruff.toml
├── requirements.txt
└── mypy.ini
```

### 4.2 模块标准目录结构

以 `project` 模块为例：

```
modules/project/
├── __init__.py
├── router.py          # APIRouter，prefix="/api/v1"
├── schemas.py         # Pydantic 请求/响应模型
├── models.py          # SQLAlchemy ORM 模型
├── service.py         # 业务逻辑层
├── repository.py      # 数据访问层（可选）
└── dependencies.py    # 模块级依赖注入
```

### 4.3 完整 API 端点清单（~98 端点）

**user 模块（14 端点）**

| Method | Path | Request/Query | Response | 说明 |
|--------|------|--------------|----------|------|
| POST | `/api/v1/auth/register` | `{email, password, name}` | `{user, access_token, refresh_token}` | 注册 |
| POST | `/api/v1/auth/login` | `{email, password}` | `{user, access_token, refresh_token}` | 登录 |
| POST | `/api/v1/auth/refresh` | `{refresh_token}` | `{access_token, refresh_token}` | 刷新令牌 |
| POST | `/api/v1/auth/logout` | — | `{}` | 登出 |
| GET | `/api/v1/auth/me` | — | `{id, email, name, avatar_url}` | 当前用户 |
| PATCH | `/api/v1/auth/me` | `{name?, avatar_url?, password?}` | `{id, email, name}` | 更新个人信息 |
| GET | `/api/v1/teams` | `?page&page_size` | `{items:[], meta}` | 团队列表 |
| POST | `/api/v1/teams` | `{name, description?}` | `{id, name, description}` | 创建团队 |
| GET | `/api/v1/teams/{id}` | — | `{id, name, description, members}` | 团队详情 |
| PATCH | `/api/v1/teams/{id}` | `{name?, description?}` | `{...}` | 更新团队 |
| DELETE | `/api/v1/teams/{id}` | — | `{}` | 删除团队 |
| POST | `/api/v1/teams/{id}/members` | `{user_id, role}` | `{team_id, user_id, role}` | 添加成员 |
| DELETE | `/api/v1/teams/{id}/members/{uid}` | — | `{}` | 移除成员 |
| GET | `/api/v1/admin/users` | `?page&search` | `{items:[], meta}` | 用户管理列表 |

**project 模块（35 端点）**

| Method | Path | Request/Query | Response | 说明 |
|--------|------|--------------|----------|------|
| POST | `/api/v1/projects` | `{name, key, description?}` | `{id, name, key, description}` | 创建项目 |
| GET | `/api/v1/projects` | `?page&search` | `{items:[], meta}` | 项目列表 |
| GET | `/api/v1/projects/{id}` | — | `{id, name, key, description, stats}` | 项目详情 |
| PATCH | `/api/v1/projects/{id}` | `{name?, description?}` | `{...}` | 更新项目 |
| DELETE | `/api/v1/projects/{id}` | — | `{}` | 软删除 |
| GET | `/api/v1/projects/{id}/members` | — | `{items:[{user_id,name,email,role}]}` | 成员列表 |
| POST | `/api/v1/projects/{id}/members` | `{user_id, role}` | `{user_id, role}` | 添加成员 |
| PATCH | `/api/v1/projects/{id}/members/{uid}` | `{role}` | `{user_id, role}` | 更新角色 |
| DELETE | `/api/v1/projects/{id}/members/{uid}` | — | `{}` | 移除成员 |
| POST | `/api/v1/projects/{id}/iterations` | `{name, start_date, end_date, goal?}` | `{id, name, ...}` | 创建迭代 |
| GET | `/api/v1/projects/{id}/iterations` | `?status` | `{items:[], meta}` | 迭代列表 |
| PATCH | `/api/v1/projects/{id}/iterations/{iid}` | `{name?, start_date?, end_date?, status?}` | `{...}` | 更新迭代 |
| DELETE | `/api/v1/projects/{id}/iterations/{iid}` | — | `{}` | 删除迭代 |
| POST | `/api/v1/projects/{id}/requirements` | `{title, description?, priority, iteration_id?, assignee_id?}` | `{id, title, ...}` | 创建需求 |
| GET | `/api/v1/projects/{id}/requirements` | `?page&status&priority&iteration_id&assignee_id&search` | `{items:[], meta}` | 需求列表 |
| GET | `/api/v1/projects/{id}/requirements/{rid}` | — | `{id, title, description, status, priority, tasks}` | 需求详情 |
| PATCH | `/api/v1/projects/{id}/requirements/{rid}` | `{title?, description?, status?, priority?, assignee_id?, iteration_id?}` | `{...}` | 更新需求 |
| DELETE | `/api/v1/projects/{id}/requirements/{rid}` | — | `{}` | 软删除需求 |
| POST | `/api/v1/projects/{id}/tasks` | `{title, description?, status, priority, assignee_id?, requirement_id?, iteration_id?, parent_id?}` | `{id, title, ...}` | 创建任务 |
| GET | `/api/v1/projects/{id}/tasks` | `?page&status&priority&assignee_id&iteration_id&requirement_id&search` | `{items:[], meta}` | 任务列表 |
| GET | `/api/v1/projects/{id}/tasks/{tid}` | — | `{id, title, description, status, priority, subtasks, comments}` | 任务详情 |
| PATCH | `/api/v1/projects/{id}/tasks/{tid}` | `{title?, description?, status?, priority?, assignee_id?, iteration_id?}` | `{...}` | 更新任务 |
| DELETE | `/api/v1/projects/{id}/tasks/{tid}` | — | `{}` | 软删除 |
| POST | `/api/v1/projects/{id}/bugs` | `{title, description?, severity, priority, assignee_id?, iteration_id?}` | `{id, title, ...}` | 创建缺陷 |
| GET | `/api/v1/projects/{id}/bugs` | `?page&severity&priority&status&assignee_id&iteration_id` | `{items:[], meta}` | 缺陷列表 |
| GET | `/api/v1/projects/{id}/bugs/{bid}` | — | `{id, title, description, severity, priority, status}` | 缺陷详情 |
| PATCH | `/api/v1/projects/{id}/bugs/{bid}` | `{title?, description?, severity?, priority?, status?, assignee_id?}` | `{...}` | 更新缺陷 |
| DELETE | `/api/v1/projects/{id}/bugs/{bid}` | — | `{}` | 软删除 |
| GET | `/api/v1/projects/{id}/board` | — | `{columns:[], cards:[]}` | 看板数据 |
| POST | `/api/v1/projects/{id}/board/columns` | `{name, order}` | `{id, name, order}` | 创建列 |
| PATCH | `/api/v1/projects/{id}/board/columns/{cid}` | `{name?, order?}` | `{...}` | 更新列 |
| DELETE | `/api/v1/projects/{id}/board/columns/{cid}` | — | `{}` | 删除列 |
| POST | `/api/v1/projects/{id}/board/cards` | `{column_id, item_type, item_id, order}` | `{id, column_id, ...}` | 添加卡片 |
| PATCH | `/api/v1/projects/{id}/board/cards/{cid}` | `{column_id?, order?}` | `{...}` | 移动卡片 |
| DELETE | `/api/v1/projects/{id}/board/cards/{cid}` | — | `{}` | 移除卡片 |

**repo 模块（6 端点）**

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/repo/connections` | 连接仓库 |
| GET | `/api/v1/projects/{id}/repo/connections` | 连接列表 |
| DELETE | `/api/v1/projects/{id}/repo/connections/{cid}` | 断开连接 |
| GET | `/api/v1/projects/{id}/repo/branches` | 分支列表 |
| GET | `/api/v1/projects/{id}/repo/commits` | 提交历史 |
| POST | `/api/v1/webhooks/{provider}` | Webhook 接收 |

**pipeline 模块（10 端点）**

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/v1/projects/{id}/pipelines` | 创建流水线 |
| GET | `/api/v1/projects/{id}/pipelines` | 流水线列表 |
| GET | `/api/v1/projects/{id}/pipelines/{pid}` | 流水线详情 |
| PATCH | `/api/v1/projects/{id}/pipelines/{pid}` | 更新流水线 |
| DELETE | `/api/v1/projects/{id}/pipelines/{pid}` | 删除流水线 |
| POST | `/api/v1/projects/{id}/pipelines/{pid}/run` | 触发执行 |
| GET | `/api/v1/projects/{id}/pipelines/{pid}/runs` | 执行历史 |
| GET | `/api/v1/projects/{id}/pipelines/{pid}/runs/{rid}` | 执行详情 |
| POST | `/api/v1/projects/{id}/pipelines/{pid}/runs/{rid}/cancel` | 取消执行 |
| WS | `/api/v1/ws/pipelines/{pid}/runs/{rid}/logs` | 实时日志 |

**artifact 模块（4 端点）** — 仓库 CRUD + 上传/列表

**test 模块（12 端点）** — 用例集/用例/测试计划/测试执行 CRUD

**deploy 模块（10 端点）** — 环境/部署任务/凭证 CRUD

**metrics 模块（4 端点）** — 吞吐/缺陷趋势/部署频率/交付周期

**notification 模块（5 端点）** — 消息列表/已读/规则 CRUD

---

## 五、数据库设计（53 表完整 DDL）

### 5.1 Schema 分布

| Schema | 归属 | 表数 | 核心表 |
|--------|------|------|--------|
| `public` | system | 1 | `alembic_version` |
| `iam` | user | 6 | users, roles, user_roles, teams, team_members, user_oauth_tokens |
| `project` | project | 14 | projects, project_members, iterations, requirements, tasks, bugs, requirement_tasks, task_dependencies, boards, board_columns, board_swimlanes, board_cards, labels, item_labels |
| `pipeline` | pipeline | 8 | pipelines, pipeline_stages, pipeline_jobs, pipeline_triggers, pipeline_runs, stage_runs, job_runs, job_logs |
| `repo` | repo | 4 | repo_connections, webhook_events, branches, commits |
| `artifact` | artifact | 4 | repositories, artifacts, docker_images, artifact_versions |
| `test` | test | 6 | test_suites, test_cases, test_plans, test_plan_cases, test_runs, test_run_results |
| `deploy` | deploy | 5 | environments, deploy_tasks, deploy_records, ssh_credentials, k8s_clusters |
| `metrics` | metrics | 2 | efficiency_snapshots, deploy_frequency |
| `notification` | notification | 3 | messages, notification_rules, webhook_configs |

### 5.2 通用字段约定

每张业务表必须包含：

| Column | Type | Constraint | Default |
|--------|------|------------|---------|
| `id` | `UUID` | `PK` | `gen_random_uuid()` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |
| `created_by` | `UUID` | `NOT NULL` | — |
| `updated_by` | `UUID` | `NOT NULL` | — |
| `deleted_at` | `TIMESTAMPTZ` | | `NULL` |

- 逻辑外键标注为 `→ target_table`，不建物理外键
- 所有 ID 使用 UUID v4
- 软删除：`WHERE deleted_at IS NULL`

### 5.3 完整列级 DDL

---

#### iam schema

**iam.users** — 用户账号

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | `gen_random_uuid()` |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | |
| `name` | `VARCHAR(100)` | `NOT NULL` | |
| `avatar_url` | `VARCHAR(500)` | | `NULL` |
| `is_active` | `BOOLEAN` | `NOT NULL` | `true` |
| `is_superadmin` | `BOOLEAN` | `NOT NULL` | `false` |
| `last_login_at` | `TIMESTAMPTZ` | | `NULL` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |
| `deleted_at` | `TIMESTAMPTZ` | | `NULL` |

Index: `idx_users_email` UNIQUE ON (`email`) WHERE `deleted_at IS NULL`

**iam.roles** — 角色定义（种子：owner, member, viewer）

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | `gen_random_uuid()` |
| `name` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | |
| `description` | `VARCHAR(255)` | | `NULL` |
| `is_system` | `BOOLEAN` | `NOT NULL` | `false` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |

**iam.user_roles** — 用户-角色关联

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `user_id` | `UUID` | `NOT NULL` → iam.users |
| `role_id` | `UUID` | `NOT NULL` → iam.roles |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` |

Unique: `uq_user_roles` ON (`user_id`, `role_id`)

**iam.teams** — 团队

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `name` | `VARCHAR(100)` | `NOT NULL` |
| `description` | `TEXT` | `NULL` |
| `created_by` | `UUID` | `NOT NULL` → iam.users |

**iam.team_members** — 团队成员

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `team_id` | `UUID` | `NOT NULL` → iam.teams |
| `user_id` | `UUID` | `NOT NULL` → iam.users |
| `role` | `VARCHAR(20)` | `NOT NULL`, `'member'` |

Unique: `uq_team_member` ON (`team_id`, `user_id`)

**iam.user_oauth_tokens** — OAuth Token

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `user_id` | `UUID` | `NOT NULL` → iam.users |
| `provider` | `VARCHAR(20)` | `NOT NULL` |
| `access_token` | `TEXT` | `NOT NULL` |
| `refresh_token` | `TEXT` | `NULL` |
| `expires_at` | `TIMESTAMPTZ` | `NULL` |
| `provider_user_id` | `VARCHAR(255)` | `NULL` |

---

#### project schema（14 表）

**project.projects** — 项目

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `name` | `VARCHAR(200)` | `NOT NULL` | |
| `key` | `VARCHAR(10)` | `UNIQUE, NOT NULL` | |
| `description` | `TEXT` | `NULL` | |
| `is_archived` | `BOOLEAN` | `NOT NULL` | `false` |

Index: `idx_projects_key` UNIQUE ON (`key`) WHERE `deleted_at IS NULL`

**project.project_members** — 项目成员

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `user_id` | `UUID` | `NOT NULL` → iam.users | |
| `role` | `VARCHAR(20)` | `NOT NULL` | `'member'` |

Unique: `uq_project_member` ON (`project_id`, `user_id`)

**project.iterations** — 迭代

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `name` | `VARCHAR(200)` | `NOT NULL` | |
| `goal` | `TEXT` | `NULL` | |
| `start_date` | `DATE` | `NOT NULL` | |
| `end_date` | `DATE` | `NOT NULL` | |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'planning'` |

Index: `idx_iterations_project` ON (`project_id`) WHERE deleted_at IS NULL
状态：planning, active, closed

**project.requirements** — 需求

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `iteration_id` | `UUID` | → iterations | |
| `title` | `VARCHAR(500)` | `NOT NULL` | |
| `description` | `TEXT` | `NULL` | |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'draft'` |
| `priority` | `VARCHAR(10)` | `NOT NULL` | `'medium'` |
| `assignee_id` | `UUID` | → iam.users | |
| `order` | `INTEGER` | `NOT NULL` | `0` |

Index: `idx_req_project` ON (`project_id`), `idx_req_iteration` ON (`iteration_id`), `idx_req_assignee` ON (`assignee_id`)
状态：draft, reviewing, in_progress, testing, done, closed
优先级：low, medium, high, critical

**project.tasks** — 任务

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `iteration_id` | `UUID` | → iterations | |
| `parent_id` | `UUID` | → tasks | |
| `title` | `VARCHAR(500)` | `NOT NULL` | |
| `description` | `TEXT` | `NULL` | |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'todo'` |
| `priority` | `VARCHAR(10)` | `NOT NULL` | `'medium'` |
| `assignee_id` | `UUID` | → iam.users | |
| `estimated_hours` | `NUMERIC(5,1)` | `NULL` | |
| `logged_hours` | `NUMERIC(5,1)` | `NULL` | |
| `due_date` | `DATE` | `NULL` | |
| `order` | `INTEGER` | `NOT NULL` | `0` |

Index: `idx_tasks_project`, `idx_tasks_assignee`, `idx_tasks_iteration`, `idx_tasks_parent`
状态：todo, in_progress, review, done, closed

**project.bugs** — 缺陷

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `iteration_id` | `UUID` | → iterations | |
| `title` | `VARCHAR(500)` | `NOT NULL` | |
| `description` | `TEXT` | `NULL` | |
| `steps_to_reproduce` | `TEXT` | `NULL` | |
| `severity` | `VARCHAR(10)` | `NOT NULL` | `'medium'` |
| `priority` | `VARCHAR(10)` | `NOT NULL` | `'medium'` |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'open'` |
| `assignee_id` | `UUID` | → iam.users | |

严重程度：low, medium, high, critical, blocker
状态：open, in_progress, resolved, closed, reopened

**project.requirement_tasks** — 需求-任务关联

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `requirement_id` | `UUID` | `NOT NULL` → requirements |
| `task_id` | `UUID` | `NOT NULL` → tasks |

Unique: `uq_req_task` ON (`requirement_id`, `task_id`)

**project.task_dependencies** — 任务依赖

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `task_id` | `UUID` | `NOT NULL` → tasks |
| `depends_on_id` | `UUID` | `NOT NULL` → tasks |
| `type` | `VARCHAR(20)` | `NOT NULL`, `'blocks'` |

Unique: `uq_task_dep` ON (`task_id`, `depends_on_id`)

**project.boards** — 看板

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `name` | `VARCHAR(100)` | `NOT NULL` | `'默认看板'` |
| `type` | `VARCHAR(20)` | `NOT NULL` | `'kanban'` |

**project.board_columns** — 看板列

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `board_id` | `UUID` | `NOT NULL` → boards | |
| `name` | `VARCHAR(100)` | `NOT NULL` | |
| `order` | `INTEGER` | `NOT NULL` | `0` |
| `wip_limit` | `INTEGER` | `NULL` | |

Index: `idx_col_board` ON (`board_id`, `order`)

**project.board_swimlanes** — 泳道

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `board_id` | `UUID` | `NOT NULL` → boards | |
| `name` | `VARCHAR(100)` | `NOT NULL` | |
| `type` | `VARCHAR(20)` | `NOT NULL` | `'none'` |
| `order` | `INTEGER` | `NOT NULL` | `0` |

类型：none, assignee, story, iteration

**project.board_cards** — 看板卡片

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `board_id` | `UUID` | `NOT NULL` → boards |
| `column_id` | `UUID` | `NOT NULL` → columns |
| `swimlane_id` | `UUID` | → swimlanes |
| `item_type` | `VARCHAR(20)` | `NOT NULL` |
| `item_id` | `UUID` | `NOT NULL` |
| `order` | `INTEGER` | `NOT NULL`, `0` |

Index: `idx_card_column` ON (`column_id`, `order`), Unique: `uq_card_item` ON (`board_id`, `item_type`, `item_id`)

**project.labels** — 标签

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `name` | `VARCHAR(50)` | `NOT NULL` | |
| `color` | `VARCHAR(7)` | `NOT NULL` | `'#6B7280'` |

Unique: `uq_label_name` ON (`project_id`, `name`) WHERE deleted_at IS NULL

**project.item_labels** — 条目-标签关联

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `label_id` | `UUID` | `NOT NULL` → labels |
| `item_type` | `VARCHAR(20)` | `NOT NULL` |
| `item_id` | `UUID` | `NOT NULL` |

Unique: `uq_label_item` ON (`label_id`, `item_type`, `item_id`)

---

#### pipeline schema（8 表）

**pipeline.pipelines** — 流水线定义

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `name` | `VARCHAR(200)` | `NOT NULL` | |
| `description` | `TEXT` | `NULL` | |
| `is_enabled` | `BOOLEAN` | `NOT NULL` | `true` |
| `run_counter` | `INTEGER` | `NOT NULL` | `0` |

**pipeline.pipeline_stages** — Stage 定义

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `pipeline_id` | `UUID` | `NOT NULL` → pipelines | |
| `name` | `VARCHAR(100)` | `NOT NULL` | |
| `order` | `INTEGER` | `NOT NULL` | `0` |
| `condition` | `VARCHAR(20)` | `NOT NULL` | `'always'` |

Index: `idx_stage_pipeline` ON (`pipeline_id`, `order`)

**pipeline.pipeline_jobs** — Job 定义

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `stage_id` | `UUID` | `NOT NULL` → stages | |
| `name` | `VARCHAR(200)` | `NOT NULL` | |
| `image` | `VARCHAR(500)` | `NOT NULL` | |
| `script` | `TEXT` | `NOT NULL` | |
| `timeout_seconds` | `INTEGER` | `NOT NULL` | `3600` |
| `order` | `INTEGER` | `NOT NULL` | `0` |
| `variables` | `JSONB` | | `'{}'` |

**pipeline.pipeline_triggers** — 触发条件

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `pipeline_id` | `UUID` | `NOT NULL` → pipelines | |
| `type` | `VARCHAR(20)` | `NOT NULL` | `'manual'` |
| `config` | `JSONB` | | `'{}'` |
| `is_enabled` | `BOOLEAN` | `NOT NULL` | `true` |

类型：manual, push, webhook, schedule

**pipeline.pipeline_runs** — 执行记录

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `pipeline_id` | `UUID` | `NOT NULL` → pipelines | |
| `run_number` | `INTEGER` | `NOT NULL` | |
| `trigger_type` | `VARCHAR(20)` | `NOT NULL` | |
| `trigger_user_id` | `UUID` | → iam.users | |
| `branch` | `VARCHAR(255)` | `NULL` | |
| `commit_sha` | `VARCHAR(40)` | `NULL` | |
| `variables` | `JSONB` | | `'{}'` |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'pending'` |
| `started_at` | `TIMESTAMPTZ` | `NULL` | |
| `finished_at` | `TIMESTAMPTZ` | `NULL` | |

Index: `idx_run_pipeline` ON (`pipeline_id`, `run_number` DESC)
状态：pending, running, success, failed, cancelled

**pipeline.stage_runs** — Stage 执行

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `run_id` | `UUID` | `NOT NULL` → runs |
| `stage_id` | `UUID` | `NOT NULL` → stages |
| `name` | `VARCHAR(100)` | `NOT NULL` |
| `status` | `VARCHAR(20)` | `NOT NULL` |
| `order` | `INTEGER` | `NOT NULL` |
| `started_at` | `TIMESTAMPTZ` | `NULL` |
| `finished_at` | `TIMESTAMPTZ` | `NULL` |

**pipeline.job_runs** — Job 执行

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `stage_run_id` | `UUID` | `NOT NULL` → stage_runs |
| `job_id` | `UUID` | `NOT NULL` → jobs |
| `name` | `VARCHAR(200)` | `NOT NULL` |
| `status` | `VARCHAR(20)` | `NOT NULL` |
| `exit_code` | `INTEGER` | `NULL` |
| `started_at` | `TIMESTAMPTZ` | `NULL` |
| `finished_at` | `TIMESTAMPTZ` | `NULL` |

**pipeline.job_logs** — 执行日志

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `job_run_id` | `UUID` | `NOT NULL` → job_runs |
| `line_number` | `INTEGER` | `NOT NULL` |
| `content` | `TEXT` | `NOT NULL` |
| `stream` | `VARCHAR(6)` | `NOT NULL` |
| `timestamp` | `TIMESTAMPTZ` | `NOT NULL` |

Index: `idx_log_job` ON (`job_run_id`, `line_number`)

---

#### repo schema（4 表）

**repo.repo_connections** — 仓库连接

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `project_id` | `UUID` | `NOT NULL` → projects |
| `provider` | `VARCHAR(20)` | `NOT NULL` |
| `repo_url` | `VARCHAR(500)` | `NOT NULL` |
| `repo_name` | `VARCHAR(200)` | `NOT NULL` |
| `oauth_token_id` | `UUID` | → iam.user_oauth_tokens |
| `webhook_secret` | `VARCHAR(255)` | `NULL` |
| `is_active` | `BOOLEAN` | `NOT NULL`, `true` |

**repo.webhook_events** — Webhook 事件

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `connection_id` | `UUID` | `NOT NULL` → connections |
| `event_type` | `VARCHAR(50)` | `NOT NULL` |
| `payload` | `JSONB` | `NOT NULL` |
| `processed` | `BOOLEAN` | `NOT NULL`, `false` |

**repo.branches** — 分支缓存

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `connection_id` | `UUID` | `NOT NULL` → connections |
| `name` | `VARCHAR(255)` | `NOT NULL` |
| `last_commit_sha` | `VARCHAR(40)` | `NULL` |
| `last_commit_message` | `TEXT` | `NULL` |
| `last_commit_author` | `VARCHAR(255)` | `NULL` |
| `last_commit_date` | `TIMESTAMPTZ` | `NULL` |

**repo.commits** — 提交记录

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `connection_id` | `UUID` | `NOT NULL` → connections |
| `branch` | `VARCHAR(255)` | `NOT NULL` |
| `sha` | `VARCHAR(40)` | `NOT NULL` |
| `message` | `TEXT` | `NOT NULL` |
| `author_name` | `VARCHAR(255)` | `NOT NULL` |
| `author_email` | `VARCHAR(255)` | `NOT NULL` |
| `committed_at` | `TIMESTAMPTZ` | `NOT NULL` |

---

#### artifact schema（4 表）

**artifact.repositories** — 制品仓库

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `name` | `VARCHAR(200)` | `NOT NULL` | |
| `type` | `VARCHAR(20)` | `NOT NULL` | `'generic'` |
| `description` | `TEXT` | `NULL` | |

**artifact.artifacts** — 制品文件

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `repository_id` | `UUID` | `NOT NULL` → repositories |
| `name` | `VARCHAR(255)` | `NOT NULL` |
| `version` | `VARCHAR(100)` | `NOT NULL` |
| `size_bytes` | `BIGINT` | `NOT NULL` |
| `storage_path` | `VARCHAR(500)` | `NOT NULL` |
| `checksum` | `VARCHAR(64)` | `NULL` |
| `metadata` | `JSONB` | `'{}'` |

**artifact.docker_images** — Docker 镜像

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `repository_id` | `UUID` | `NOT NULL` → repositories |
| `image_name` | `VARCHAR(255)` | `NOT NULL` |
| `tag` | `VARCHAR(100)` | `NOT NULL` |
| `digest` | `VARCHAR(71)` | `NULL` |
| `size_bytes` | `BIGINT` | `NULL` |
| `pushed_by` | `UUID` | `NOT NULL` → iam.users |

**artifact.artifact_versions** — 版本元数据

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `repository_id` | `UUID` | `NOT NULL` → repositories |
| `version` | `VARCHAR(100)` | `NOT NULL` |
| `release_notes` | `TEXT` | `NULL` |
| `pipeline_run_id` | `UUID` | → pipeline.runs |

Unique: `uq_av_repo_version` ON (`repository_id`, `version`)

---

#### test schema（6 表）

**test.test_suites** — 用例集

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `project_id` | `UUID` | `NOT NULL` → projects |
| `name` | `VARCHAR(200)` | `NOT NULL` |
| `description` | `TEXT` | `NULL` |
| `parent_id` | `UUID` | → test_suites |

**test.test_cases** — 测试用例

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `suite_id` | `UUID` | `NOT NULL` → suites | |
| `title` | `VARCHAR(500)` | `NOT NULL` | |
| `steps` | `TEXT` | `NOT NULL` | |
| `expected` | `TEXT` | `NOT NULL` | |
| `priority` | `VARCHAR(10)` | `NOT NULL` | `'medium'` |
| `type` | `VARCHAR(20)` | `NOT NULL` | `'manual'` |

**test.test_plans** — 测试计划

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `iteration_id` | `UUID` | → project.iterations | |
| `name` | `VARCHAR(200)` | `NOT NULL` | |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'draft'` |

状态：draft, active, completed

**test.test_plan_cases** — 计划-用例关联

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `plan_id` | `UUID` | `NOT NULL` → plans |
| `case_id` | `UUID` | `NOT NULL` → cases |
| `order` | `INTEGER` | `NOT NULL`, `0` |

Unique: `uq_plan_case` ON (`plan_id`, `case_id`)

**test.test_runs** — 测试执行

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `plan_id` | `UUID` | `NOT NULL` → plans | |
| `environment_id` | `UUID` | → deploy.environments | |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'pending'` |
| `started_by` | `UUID` | `NOT NULL` → iam.users | |
| `started_at` | `TIMESTAMPTZ` | `NULL` | |
| `finished_at` | `TIMESTAMPTZ` | `NULL` | |

状态：pending, in_progress, completed

**test.test_run_results** — 用例执行结果

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `run_id` | `UUID` | `NOT NULL` → runs | |
| `case_id` | `UUID` | `NOT NULL` → cases | |
| `status` | `VARCHAR(10)` | `NOT NULL` | `'pending'` |
| `comment` | `TEXT` | `NULL` | |
| `executed_by` | `UUID` | → iam.users | |
| `executed_at` | `TIMESTAMPTZ` | `NULL` | |

Unique: `uq_run_case` ON (`run_id`, `case_id`)
状态：pending, pass, fail, skip, blocked

---

#### deploy schema（5 表）

**deploy.environments** — 环境定义

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `name` | `VARCHAR(100)` | `NOT NULL` | |
| `type` | `VARCHAR(20)` | `NOT NULL` | `'ssh'` |
| `config` | `JSONB` | `NOT NULL` | `'{}'` |
| `is_protected` | `BOOLEAN` | `NOT NULL` | `false` |

**deploy.deploy_tasks** — 部署任务

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `environment_id` | `UUID` | `NOT NULL` → environments | |
| `artifact_id` | `UUID` | → artifact.artifacts | |
| `branch` | `VARCHAR(255)` | `NULL` | |
| `commit_sha` | `VARCHAR(40)` | `NULL` | |
| `strategy` | `VARCHAR(20)` | `NOT NULL` | `'rolling'` |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'pending'` |
| `trigger_user_id` | `UUID` | `NOT NULL` → iam.users | |
| `started_at` | `TIMESTAMPTZ` | `NULL` | |
| `finished_at` | `TIMESTAMPTZ` | `NULL` | |

状态：pending, running, success, failed, rolled_back

**deploy.deploy_records** — 部署记录

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `task_id` | `UUID` | `NOT NULL` → tasks |
| `environment_id` | `UUID` | `NOT NULL` → environments |
| `status` | `VARCHAR(20)` | `NOT NULL` |
| `log` | `TEXT` | `NULL` |
| `deployed_by` | `UUID` | `NOT NULL` → iam.users |
| `deployed_at` | `TIMESTAMPTZ` | `NOT NULL` |

**deploy.ssh_credentials** — SSH 凭证

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `name` | `VARCHAR(100)` | `NOT NULL` | |
| `host` | `VARCHAR(255)` | `NOT NULL` | |
| `port` | `INTEGER` | `NOT NULL` | `22` |
| `username` | `VARCHAR(100)` | `NOT NULL` | |
| `private_key_encrypted` | `TEXT` | `NOT NULL` | |

**deploy.k8s_clusters** — K8s 集群（后期）

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `name` | `VARCHAR(100)` | `NOT NULL` |
| `kubeconfig_encrypted` | `TEXT` | `NOT NULL` |

---

#### metrics schema（2 表）

**metrics.efficiency_snapshots** — 效能快照

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `snapshot_date` | `DATE` | `NOT NULL` | |
| `open_requirements` | `INTEGER` | `NOT NULL` | `0` |
| `completed_requirements` | `INTEGER` | `NOT NULL` | `0` |
| `open_bugs` | `INTEGER` | `NOT NULL` | `0` |
| `resolved_bugs` | `INTEGER` | `NOT NULL` | `0` |
| `deploy_count` | `INTEGER` | `NOT NULL` | `0` |
| `avg_lead_time_hours` | `NUMERIC(8,2)` | `NULL` | |

Unique: `uq_snapshot` ON (`project_id`, `snapshot_date`)

**metrics.deploy_frequency** — 部署频率

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `UUID` | `PK` |
| `project_id` | `UUID` | `NOT NULL` → projects |
| `environment_id` | `UUID` | `NOT NULL` → deploy.environments |
| `deploy_date` | `DATE` | `NOT NULL` |
| `count` | `INTEGER` | `NOT NULL`, `0` |

Unique: `uq_deploy_freq` ON (`project_id`, `environment_id`, `deploy_date`)

---

#### notification schema（3 表）

**notification.messages** — 站内消息

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `user_id` | `UUID` | `NOT NULL` → iam.users | |
| `type` | `VARCHAR(50)` | `NOT NULL` | |
| `title` | `VARCHAR(500)` | `NOT NULL` | |
| `content` | `TEXT` | `NULL` | |
| `link` | `VARCHAR(500)` | `NULL` | |
| `is_read` | `BOOLEAN` | `NOT NULL` | `false` |
| `read_at` | `TIMESTAMPTZ` | `NULL` | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `now()` |

Index: `idx_msg_user` ON (`user_id`, `is_read`, `created_at` DESC)

**notification.notification_rules** — 通知规则

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `event` | `VARCHAR(50)` | `NOT NULL` | |
| `channel` | `VARCHAR(20)` | `NOT NULL` | `'in_app'` |
| `config` | `JSONB` | `NOT NULL` | `'{}'` |
| `is_enabled` | `BOOLEAN` | `NOT NULL` | `true` |

**notification.webhook_configs** — Webhook 配置

| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | `UUID` | `PK` | |
| `project_id` | `UUID` | `NOT NULL` → projects | |
| `url` | `VARCHAR(500)` | `NOT NULL` | |
| `secret` | `VARCHAR(255)` | `NULL` | |
| `events` | `JSONB` | `NOT NULL` | `'[]'` |
| `is_active` | `BOOLEAN` | `NOT NULL` | `true` |

### 5.4 索引策略

- 所有逻辑外键列建 B-Tree 索引
- 软删除查询列建部分索引 `WHERE deleted_at IS NULL`
- 唯一约束使用部分索引（排除已删除行）
- 时间范围查询列按 DESC 排序建索引

---

## 六、前端工程结构

### 6.1 目录结构

```
frontend/
├── src/
│   ├── App.vue                        # n-config-provider + RouterView
│   ├── main.ts                        # Naive UI 全局注册
│   ├── router/index.ts                # 路由守卫 + 权限
│   ├── stores/                        # Pinia
│   │   ├── auth.ts                    # {user, tokens, isAuthenticated}
│   │   ├── project.ts                 # {currentProject, permissions}
│   │   └── board.ts                   # {columns, cards, dragState}
│   ├── api/                           # Axios 封装
│   │   ├── client.ts                  # 实例 + token 刷新拦截器
│   │   ├── auth.ts, projects.ts, requirements.ts, tasks.ts
│   │   ├── bugs.ts, iterations.ts, board.ts, pipelines.ts
│   │   ├── repos.ts, tests.ts, deploys.ts, metrics.ts, notifications.ts
│   ├── views/
│   │   ├── auth/LoginView.vue, RegisterView.vue
│   │   ├── dashboard/DashboardView.vue
│   │   ├── project/
│   │   │   ├── ProjectListView.vue, ProjectDetailView.vue
│   │   │   ├── BoardView.vue
│   │   │   ├── RequirementListView.vue, RequirementDetailView.vue
│   │   │   ├── TaskListView.vue, TaskDetailView.vue
│   │   │   ├── BugListView.vue, BugDetailView.vue
│   │   │   ├── IterationListView.vue
│   │   │   ├── SettingsView.vue, MetricsView.vue
│   │   ├── pipeline/PipelineListView.vue, PipelineEditView.vue, PipelineRunView.vue
│   │   ├── test/TestSuiteListView.vue, TestCaseListView.vue, TestPlanListView.vue, TestRunView.vue
│   │   ├── deploy/EnvironmentListView.vue, DeployHistoryView.vue
│   │   └── admin/UserManagementView.vue, TeamManagementView.vue
│   ├── components/
│   │   ├── common/
│   │   │   ├── AppLayout.vue           # Header + Sidebar + Content
│   │   │   ├── AppHeader.vue           # Logo + 用户菜单 + 通知
│   │   │   ├── AppSidebar.vue          # 项目导航
│   │   │   ├── StatusTag.vue, PriorityTag.vue, UserAvatar.vue
│   │   │   ├── UserSelector.vue        # 远程搜索用户
│   │   │   ├── EmptyState.vue, LoadingOverlay.vue
│   │   │   ├── ConfirmDialog.vue, PageHeader.vue
│   │   │   └── MarkdownEditor.vue
│   │   ├── project/
│   │   │   ├── BoardColumn.vue         # 列容器 + WIP 限制
│   │   │   ├── BoardCard.vue           # 卡片（类型/标题/标签/指派人）
│   │   │   ├── RequirementForm.vue, TaskForm.vue, BugForm.vue
│   │   │   ├── ItemDetailDrawer.vue    # 复用详情抽屉
│   │   │   ├── IterationTimeline.vue
│   │   │   ├── LabelManager.vue, MemberManager.vue
│   │   └── pipeline/
│   │       ├── StageCard.vue, JobConfigForm.vue
│   │       ├── LogViewer.vue           # 虚拟滚动 + 搜索
│   │       └── PipelineStatusBadge.vue
│   ├── composables/
│   │   ├── useAuth.ts, usePagination.ts, useWebSocket.ts
│   │   ├── useDebounce.ts, usePermission.ts, useNotification.ts
│   ├── types/                          # TS 类型，与后端 schemas 对应
│   │   ├── api.ts, auth.ts, project.ts, pipeline.ts, deploy.ts, test.ts, board.ts, notification.ts
│   ├── utils/date.ts, format.ts, constants.ts
│   └── assets/styles/variables.css, global.css
├── package.json, pnpm-lock.yaml, tsconfig.json, vite.config.ts
├── .eslintrc.cjs, .prettierrc
└── Dockerfile
```

### 6.2 路由表

```
/login                        — 登录
/register                     — 注册
/dashboard                    — 仪表盘

/projects                     — 项目列表
/projects/:id                 — 项目概览
/projects/:id/board           — 看板
/projects/:id/requirements    — 需求列表
/projects/:id/requirements/:rid — 需求详情
/projects/:id/tasks           — 任务列表
/projects/:id/tasks/:tid     — 任务详情
/projects/:id/bugs            — 缺陷列表
/projects/:id/bugs/:bid      — 缺陷详情
/projects/:id/iterations      — 迭代
/projects/:id/pipelines       — 流水线列表
/projects/:id/pipelines/:pid  — 流水线编辑
/projects/:id/pipelines/:pid/runs/:rid — 执行日志
/projects/:id/tests/suites    — 用例集
/projects/:id/tests/cases     — 用例列表
/projects/:id/tests/plans     — 测试计划
/projects/:id/tests/plans/:pid/run — 测试执行
/projects/:id/deploy          — 部署管理
/projects/:id/metrics         — 效能度量
/projects/:id/settings        — 项目设置

/admin/users                  — 用户管理
/admin/teams                  — 团队管理
```

### 6.3 前端设计约束

- **信息密度优先**：看板/列表/仪表盘紧凑，`n-table size="small"`
- **图标优先**：按钮使用 `n-button` + Lucide 图标，文字按钮仅用于"保存""取消"
- **无 Landing Page**：`/` 重定向 `/dashboard`
- **无渐变/bokeh**：背景纯色浅灰
- **卡片使用**：仅列表重复条目使用 `n-card`，页面区域不包裹
- **字体**：不随视口缩放，`letter-spacing: 0`
- **主题**：Naive UI 亮色主题，品牌色 `#2080F0`
- **布局固定**：Header 56px，Sidebar 240px（可折叠 64px），CSS Grid 固钉

### 6.4 关键组件接口

**BoardColumn.vue**
```
Props: { column: BoardColumn, cards: BoardCard[], wipLimit?: number }
Emits: { addCard, moveCard }
```

**BoardCard.vue**
```
Props: { card: BoardCard, isDragging: boolean }
Emits: { click, contextmenu }
```

**ItemDetailDrawer.vue**
```
Props: { itemType: 'requirement'|'task'|'bug', itemId: string, visible: boolean }
Emits: { close, updated }
```

**LogViewer.vue**
```
Props: { jobRunId: string, autoscroll: boolean }
Uses: useWebSocket composable
Features: 虚拟滚动 + 搜索高亮 + stdout/stderr 颜色区分
```

**UserSelector.vue**
```
Props: { modelValue: string|null, projectId: string, placeholder: string }
Emits: { 'update:modelValue' }
Features: 远程搜索 + 防抖 300ms
```

---

## 七、API 设计约定

### 7.1 URL 与 HTTP 方法

```
GET    /api/v1/projects              # 列表
POST   /api/v1/projects              # 创建
GET    /api/v1/projects/{id}         # 详情
PATCH  /api/v1/projects/{id}         # 部分更新
DELETE /api/v1/projects/{id}         # 软删除
```

### 7.2 响应格式

```json
// 单条：{ "data": { "id": "uuid", "name": "..." } }
// 分页：{ "data": [...], "meta": { "page": 1, "page_size": 20, "total": 100 } }
// 错误：{ "error": { "code": "PROJECT_NOT_FOUND", "message": "项目不存在" } }
```

### 7.3 认证

- JWT Bearer Token，过期 24h
- Refresh Token 存 Redis（key: `refresh:{user_id}`，过期 7 天）
- 除 `/api/v1/auth/*` 外均需认证
- 限流：单用户 100 req/min（Redis 滑动窗口）

### 7.4 错误码

| 错误码 | HTTP | 场景 |
|--------|------|------|
| `VALIDATION_ERROR` | 422 | Pydantic 校验失败 |
| `UNAUTHORIZED` | 401 | Token 缺失/过期 |
| `FORBIDDEN` | 403 | 无项目权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 唯一约束冲突 |
| `RATE_LIMITED` | 429 | 频率超限 |
| `INTERNAL_ERROR` | 500 | 未预期异常 |
| `PIPELINE_RUNNING` | 409 | 流水线已在执行 |
| `DEPLOY_BLOCKED` | 409 | 环境受保护 |

---

## 八、Docker Compose 部署

### 8.1 docker-compose.yml

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-devops_platform}
      POSTGRES_USER: ${POSTGRES_USER:-devops}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devops123}
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/init_db.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-devops}"]
      interval: 5s; timeout: 5s; retries: 10

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: [redis_data:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s; timeout: 3s; retries: 10

  api:
    build: { context: ./backend, dockerfile: Dockerfile }
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-devops}:${POSTGRES_PASSWORD:-devops123}@postgres:5432/${POSTGRES_DB:-devops_platform}
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET:-dev-secret}
      LOG_LEVEL: INFO
    ports: ["8000:8000"]
    volumes:
      - ./backend:/app
      - artifact_storage:/var/artifacts
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }

  worker:
    build: { context: ./backend, dockerfile: Dockerfile }
    command: python -m app.worker
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-devops}:${POSTGRES_PASSWORD:-devops123}@postgres:5432/${POSTGRES_DB:-devops_platform}
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend:/app
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on: [postgres, redis]

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on: [api]

volumes:
  postgres_data:
  redis_data:
  artifact_storage:
```

### 8.2 Nginx 配置

```nginx
upstream api { server api:8000; }
server {
    listen 80;
    client_max_body_size 100M;
    location /api/v1/ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 8.3 Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/api/v1/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 8.4 启动流程

```
docker compose up -d
→ postgres healthy → init_db.sql 创建 schema
→ redis healthy
→ api → alembic upgrade head → healthy
→ worker 启动
→ nginx 启动
→ http://localhost → /dashboard
```

---

## 九、分阶段开发计划

### Phase 0：项目骨架

**目标**：可一键启动的空壳

1. 仓库根目录 + `.gitignore` + `README.md`
2. `docker-compose.yml` + `nginx/default.conf`
3. `backend/Dockerfile` + `frontend/Dockerfile`
4. FastAPI 骨架：`main.py`, `config.py`, `dependencies.py`, 异常处理, JWT, `GET /api/v1/health`
5. SQLAlchemy Base + Alembic 初始化
6. Vue3 + Vite + Naive UI + Router + Pinia + Axios
7. `LoginView.vue`（仅 UI）+ `DashboardView.vue`（显示版本号）
8. `AppLayout.vue`（Header + Sidebar 骨架）
9. `docker compose up` 验证完整链路

### Phase 1：IAM + 项目管理

1. iam + project 全部 20 张表 DDL + migration
2. user 模块：注册/登录/JWT/团队 CRUD
3. project 模块：项目/成员/迭代/需求/任务/缺陷/看板/标签 全部端点
4. 种子数据脚本
5. 前端全部对应页面 + 看板拖拽

### Phase 2：CI/CD

1. pipeline + repo 全部 12 张表
2. 仓库 OAuth 对接 + Webhook
3. 流水线定义 + 执行引擎（Worker + Redis 队列 + Docker in Docker）
4. WebSocket 实时日志
5. 前端：流水线编辑器 + 执行详情 + LogViewer

### Phase 3：测试 + 部署 + 制品

1. test + deploy + artifact 全部 15 张表
2. 测试用例/计划/执行 + 环境管理 + SSH 部署 + 制品上传

### Phase 4：度量 + 通知 + 发布

1. metrics + notification 全部 5 张表
2. 效能看板 + 站内通知 + Webhook
3. 每日快照定时任务
4. 全链路测试 + 文档 + v0.1.0-alpha

---

## 十、质量门禁

每个 Phase 交付前：

- [ ] 所有 API 有 Pydantic schema 定义
- [ ] 所有 API 路由在 OpenAPI `/docs` 可见可交互
- [ ] 后端 service 层测试覆盖率 ≥80%
- [ ] 前端 ESLint + TypeScript strict 零错误
- [ ] `docker compose up` 一键启动无报错
- [ ] Alembic migration 双向执行无报错
- [ ] 所有 DB 查询在事务中执行
- [ ] 无 `print()` / `console.log()` 残留
- [ ] 所有列表接口支持分页
- [ ] 所有软删除资源正确过滤

---

## 十一、关键风险

| 风险 | 影响 | 对策 |
|------|------|------|
| 53 表范围过大 | 高 | 按 Phase 拆分建表，不提前建全部 |
| 流水线引擎复杂度 | 高 | MVP 仅单 Stage Shell，Docker in Docker，不做状态机 |
| 看板拖拽冲突 | 中 | 乐观更新 + order 整数间隙（间隔 1000）+ 409 回滚 |
| 权限模型过度设计 | 低 | 仅项目级 RBAC |
| Worker 容器执行 Docker | 中 | 挂载 `docker.sock` + 镜像白名单 |
| WebSocket 连接泄漏 | 中 | 30s 心跳 + onUnmounted 断开 + 5min 超时清理 |

---

## 十二、开发环境

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.11 | 后端 |
| Node.js | ≥20 LTS | 前端 |
| pnpm | ≥9 | 包管理 |
| Docker | ≥24 + Compose v2 | 容器化 |
| psql | ≥15 | 数据库调试 |

---

## 十三、测试策略

### 测试层次

| 层次 | 工具 | 覆盖率 | 运行时机 |
|------|------|--------|---------|
| 后端单元测试 | pytest + pytest-asyncio | ≥80% | CI 每次提交 |
| API 集成测试 | httpx.AsyncClient | 所有端点 ≥1 成功路径 | CI 合并 |
| 前端组件测试 | vitest + @vue/test-utils | 关键组件 | CI 提交 |
| E2E | Playwright | 不强制 | 发版前 |

### 测试文件组织

```
backend/tests/
├── conftest.py               # async_session, client, auth_headers, seed_project
├── modules/
│   ├── user/test_auth.py, test_teams.py
│   ├── project/test_projects.py, test_requirements.py, test_tasks.py, test_bugs.py, test_iterations.py, test_board.py
│   ├── pipeline/test_pipelines.py, test_runs.py
│   ├── deploy/test_deploy.py
│   ├── test/test_test_cases.py
│   └── repo/test_connections.py
```

### 测试约定

- 每个测试独立，事务隔离，结束自动 rollback
- Mock 外部依赖（GitLab API, Docker daemon, SSH）
- 工厂模式创建测试数据（UserFactory, ProjectFactory）

---

## 十四、后台任务队列

### Redis 队列模型

```
API (Producer)          Worker (Consumer)
    RPUSH "queue:pipeline"
    ─────────────────►   BLPOP → Docker 容器执行 → 日志入库 + WebSocket 推送
```

| 队列 | 职责 | 并发 |
|------|------|------|
| `queue:pipeline` | 流水线执行 | 3 |
| `queue:deploy` | 部署任务 | 2 |
| `queue:notification` | 异步通知 | 1 |
| `queue:cron` | 效能快照 | 1 |

### 任务消息格式

```json
{
    "task_type": "pipeline_run",
    "payload": {
        "run_id": "uuid", "pipeline_id": "uuid", "job_id": "uuid",
        "image": "python:3.12-slim",
        "script": "pip install -r requirements.txt && pytest",
        "variables": {}
    },
    "enqueued_at": "2026-08-03T12:00:00Z",
    "retry_count": 0, "max_retries": 1
}
```

---

## 十五、日志与监控

### 日志格式（JSON）

```json
{
    "timestamp": "2026-08-03T12:00:00.000Z",
    "level": "INFO",
    "logger": "app.modules.pipeline.service",
    "message": "Pipeline run started",
    "request_id": "uuid",
    "user_id": "uuid",
    "project_id": "uuid",
    "extra": {"run_id": "uuid"}
}
```

### 日志级别约定

| 级别 | 场景 |
|------|------|
| DEBUG | SQL 语句（仅开发环境） |
| INFO | 请求入口/出口（method+path+status+latency）、流水线启停 |
| WARNING | 限流触发、Refresh Token 过期、第三方 API 重试 |
| ERROR | 未捕获异常、第三方 API 最终失败、DB 连接丢失 |
| CRITICAL | 应用无法启动 |

### 健康检查

```
GET /api/v1/health
→ { "status": "ok", "version": "0.1.0", "checks": {"database": "ok", "redis": "ok"}, "uptime_seconds": 3600 }
```

---

## 十六、CI/CD 配置

### pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff; args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0
    hooks:
      - id: mypy; args: [--strict]
```

### GitHub Actions

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:15, env: { POSTGRES_DB: test, POSTGRES_USER: test, POSTGRES_PASSWORD: test } }
      redis: { image: redis:7 }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5; with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - run: ruff check backend/ && mypy backend/
      - run: pytest backend/tests/ --cov=backend/app

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4; with: { version: 9 }
      - run: cd frontend && pnpm install --frozen-lockfile && pnpm lint && pnpm build
