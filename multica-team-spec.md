# multica 测试与评审团队运行规范

> 配套文件：`qa-agent-tasks.md`、`agents/`  
> 目标：把角色职责说明书补齐为可被 multica 编排运行的团队契约  
> 更新时间：2026-08-13

## 1. 目标与限制

本文件定义 QA 测试、代码评审和作者 Agent 在 multica 中的运行方式。它不是某种专有 SDK 配置，而是平台无关的多 Agent 运行契约。

如果 `multica` 有官方 manifest、Tool API、沙箱或状态机格式，本文件还需要映射到官方 schema；当前工作区没有这些配置文件。

## 2. 团队拓扑

```text
                          LEAD-QA
                             |
        +--------------------+-----------------------+
        |                    |                       |
  AGT-CODE-REVIEW      QA 专业 Agents           DEV-AUTHOR-{module}
        |                    |                       |
        +--------------------+-----------------------+
                    Shared Artifacts
```

### 2.1 Agent 清单

| Agent ID | 角色 | 运行权限 | 主要输出 |
| --- | --- | --- | --- |
| `LEAD-QA` | 队长 | 调度、读所有输出、写状态与裁决 | 任务状态、验收结论 |
| `AGT-CODE-REVIEW` | 代码评审 | 只读代码和 diff、写评审报告 | 评审报告 |
| `AGT-BACKEND-UNIT` | 后端测试设计 | 读规范、写后端测试设计 | 后端测试设计 |
| `AGT-API-INTEGRATION` | API 测试设计 | 读规范、写 API 测试设计 | API 测试矩阵 |
| `AGT-FRONTEND-COMPONENT` | 前端测试设计 | 读规范、写前端测试设计 | 前端组件测试设计 |
| `AGT-E2E-RELEASE` | E2E 与发布验收 | 读规范、写 E2E/发布清单 | E2E 与发布清单 |
| `AGT-INFRA-GATE` | 质量门禁 | 读规范和运行结果、写门禁清单 | 门禁清单 |
| `DEV-AUTHOR-{module}` | 模块作者 | 写对应模块代码和测试、运行验证 | 修复 diff、验证记录 |

### 2.2 作者 Agent 模块映射

| 模块 | 作者 Agent | 主要路径 |
| --- | --- | --- |
| IAM | `DEV-AUTHOR-iam` | `backend/app/modules/user/` |
| 项目 | `DEV-AUTHOR-project` | `backend/app/modules/project/` |
| 仓库 | `DEV-AUTHOR-repo` | `backend/app/modules/repo/` |
| 流水线 | `DEV-AUTHOR-pipeline` | `backend/app/modules/pipeline/` |
| 制品 | `DEV-AUTHOR-artifact` | `backend/app/modules/artifact/` |
| 测试管理 | `DEV-AUTHOR-test` | `backend/app/modules/test/` |
| 部署 | `DEV-AUTHOR-deploy` | `backend/app/modules/deploy/` |
| 度量 | `DEV-AUTHOR-metrics` | `backend/app/modules/metrics/` |
| 通知 | `DEV-AUTHOR-notification` | `backend/app/modules/notification/` |
| 前端 | `DEV-AUTHOR-frontend` | `frontend/` |
| 基础设施 | `DEV-AUTHOR-infra` | `docker/`、`backend/alembic/`、CI 配置 |

## 3. 统一状态机

所有 Agent 任务必须使用以下状态：

| 状态 | 含义 | 允许下一状态 |
| --- | --- | --- |
| `queued` | 已由 `LEAD-QA` 下发 | `running`、`cancelled` |
| `running` | Agent 正在执行 | `blocked`、`completed`、`failed`、`cancelled` |
| `blocked` | 缺少输入或外部依赖 | `running`、`cancelled` |
| `completed` | Agent 完成输出 | `approved`、`changes_requested` |
| `failed` | Agent 执行异常 | `queued`、`cancelled` |
| `changes_requested` | 评审要求修改 | `running`、`cancelled` |
| `approved` | 评审通过 | `verified` |
| `verified` | 作者验证完成且评审通过 | 终结状态 |
| `cancelled` | 任务终止 | 终结状态 |

代码评审闭环状态：

```text
queued -> running -> completed
                          |
                 +--------+--------+
                 |                 |
            approved          changes_requested
                 |                 |
                 v                 v
              verified        queued/running
                                     |
                                     v
                                 re-review
```

## 4. 消息协议

### 4.1 任务消息

```json
{
  "task_id": "QA-TASK-001",
  "agent_id": "AGT-CODE-REVIEW",
  "status": "queued",
  "source_spec": "./plan.md",
  "scope": {
    "modules": ["pipeline"],
    "files": ["backend/app/modules/pipeline/service.py"]
  },
  "input_artifacts": [],
  "output_artifacts": ["code-review-report.md"],
  "owner_agent": "LEAD-QA",
  "priority": "high",
  "retry_policy": {
    "max_retries": 2,
    "backoff_seconds": 5
  }
}
```

### 4.2 评审结果消息

```json
{
  "task_id": "QA-TASK-001",
  "agent_id": "AGT-CODE-REVIEW",
  "status": "changes_requested",
  "findings": [
    {
      "id": "CR-001",
      "severity": "high",
      "file": "backend/app/modules/pipeline/service.py",
      "line": 42,
      "problem": "Missing transaction boundary for run state update",
      "required_author_action": "Wrap DB update in transaction and add rollback test",
      "verification_commands": [
        "pytest backend/tests/modules/pipeline/test_runs.py",
        "mypy backend/"
      ]
    }
  ],
  "next_agent": "DEV-AUTHOR-pipeline",
  "resubmit_required": true
}
```

### 4.3 作者返回消息

```json
{
  "task_id": "QA-TASK-001",
  "agent_id": "DEV-AUTHOR-pipeline",
  "status": "completed",
  "changed_files": ["backend/app/modules/pipeline/service.py"],
  "verification": [
    {
      "command": "pytest backend/tests/modules/pipeline/test_runs.py",
      "exit_code": 0,
      "summary": "12 passed"
    },
    {
      "command": "mypy backend/",
      "exit_code": 0,
      "summary": "Success: no issues found"
    }
  ],
  "new_diff": "pipeline-run-transaction.diff"
}
```

## 5. 工件协议

所有 Agent 输出写入统一工件区，不得用自然语言代替结构化结果。

### 5.1 工件目录

```text
artifacts/
├── tasks/
│   └── QA-TASK-001.json
├── reviews/
│   └── QA-TASK-001-review.json
├── qa/
│   ├── backend-unit-matrix.md
│   ├── api-integration-matrix.md
│   ├── frontend-component-matrix.md
│   ├── e2e-release-checklist.md
│   └── infra-gate-checklist.md
├── author/
│   └── QA-TASK-001-fix.diff
└── status/
    └── phase-status.json
```

### 5.2 工件字段

每个工件至少包含：

- `agent_id`
- `task_id`
- `created_at`
- `input_artifacts`
- `output_artifacts`
- `status`
- `handoffs`
- `gaps`
- `risks`

## 6. 权限与沙箱

| Agent | 代码仓库 | 测试代码 | 工件区 | 外部服务 |
| --- | --- | --- | --- | --- |
| `LEAD-QA` | 只读 | 只读 | 读写 | 不调用 |
| `AGT-CODE-REVIEW` | 只读 | 只读 | 写评审 | 不调用 |
| `AGT-BACKEND-UNIT` | 只读 | 只读 | 写设计 | Mock 定义 |
| `AGT-API-INTEGRATION` | 只读 | 只读 | 写设计 | Mock 定义 |
| `AGT-FRONTEND-COMPONENT` | 只读 | 只读 | 写设计 | Mock 定义 |
| `AGT-E2E-RELEASE` | 只读 | 只读 | 写设计 | 仅 Mock 或临时测试环境 |
| `AGT-INFRA-GATE` | 只读 | 只读 | 写门禁 | 只读健康检查 |
| `DEV-AUTHOR-{module}` | 写对应模块 | 写对应测试 | 写修复 diff | 仅验证所需 |

## 7. 工具权限

| 工具类别 | 允许 Agent |
| --- | --- |
| 文件读取 | 所有 Agent |
| 文件写入 | `DEV-AUTHOR-{module}`、`LEAD-QA` 状态写入 |
| Shell 只读命令 | QA Agent、`AGT-CODE-REVIEW` |
| Shell 验证命令 | `DEV-AUTHOR-{module}`、`AGT-INFRA-GATE` |
| Docker Compose | `AGT-INFRA-GATE`、`AGT-E2E-RELEASE` |
| 网络调用 | 默认禁止，需要 `LEAD-QA` 授权 |
| 密钥读取 | 默认禁止 |

## 8. 代码评审闭环

### 8.1 正常闭环

```text
LEAD-QA
  -> AGT-CODE-REVIEW
       -> APPROVED
       -> AGT-INFRA-GATE
       -> verified

LEAD-QA
  -> AGT-CODE-REVIEW
       -> CHANGES_REQUESTED
       -> DEV-AUTHOR-{module}
       -> 修改 + 验证
       -> AGT-CODE-REVIEW
       -> APPROVED
       -> verified
```

### 8.2 复审上限

- 同一变更最多执行 2 次 `CHANGES_REQUESTED`。
- 第 3 次仍不通过时，`AGT-CODE-REVIEW` 输出 `blocked`。
- `LEAD-QA` 决定是否需要人工评审、拆分任务或标记为发布阻塞。

### 8.3 人工升级

以下情况必须升级到人工或 `LEAD-QA`：

- `critical` 安全问题。
- 数据库 migration 无法安全回滚。
- 外部凭据或密钥相关变更。
- 生产环境部署相关变更。
- 连续 2 次复审未通过。
- Agent 对边界归属无法达成一致。

## 9. 并发与重试

| 控制项 | 规则 |
| --- | --- |
| 独立任务并发 | 默认 3 |
| 同一文件写入 Agent | 1 |
| 同一模块作者 Agent | 1 |
| 任务最大重试 | 2 |
| 重试退避 | 5 秒、15 秒 |
| 超时 | 普通 QA 30 分钟，代码评审 60 分钟 |
| 失败后处理 | 转 `LEAD-QA`，不自动覆盖现有输出 |

## 10. 上下文与知识注入

每个 Agent 至少注入：

- `plan.md`
- 对应独立 Agent 文档。
- 当前 Phase 范围。
- 最近一次评审结论。
- 相关模块的已有工件。
- 边界规则和权限表。

禁止注入：

- 无关模块完整代码。
- 真实凭据、密钥、Token。
- 未经 `LEAD-QA` 确认的假设作为事实。

## 11. 可观测性

每次团队运行记录：

- `task_id`
- `agent_id`
- `status`
- `started_at`
- `completed_at`
- `attempt`
- `artifacts`
- `handoffs`
- `blocking_issues`

Phase 验收汇总：

```json
{
  "phase": "2",
  "status": "blocked",
  "review": {
    "approved": 6,
    "changes_requested": 1,
    "re_review_remaining": 1
  },
  "qa": {
    "backend_unit": "ready",
    "api_integration": "ready",
    "frontend_component": "pending",
    "e2e_release": "pending"
  },
  "infra_gate": "pending",
  "blockers": ["CR-001"]
}
```

## 12. 与现有文档的映射

| 现有文档 | 本规范作用 |
| --- | --- |
| `qa-agent-tasks.md` | 提供团队总览和职责边界 |
| `qa-acceptance-matrix.md` | 提供 Phase 0-4 验收和退出条件 |
| `agents/LEAD-QA.md` | 定义队长任务 |
| `agents/AGT-CODE-REVIEW.md` | 定义评审规则 |
| `agents/AGT-BACKEND-UNIT.md` 等 | 定义专业测试输出 |
| 本文件 | 定义运行状态、消息、工件、权限、并发和升级 |
| `agents/DEV-AUTHOR.md` | 定义作者 Agent 的修改和验证协议 |

## 13. 完全适配前必须确认

如果 `multica` 是具体运行时，以下字段必须按官方 schema 确认：

- Agent manifest 文件格式。
- Tool 调用格式。
- 沙箱和文件系统权限表达方式。
- 任务、消息、状态机的原生表达方式。
- 外部 Agent 或人工审批的接入方式。
- 是否支持结构化工件和共享内存。

在缺少这些官方格式前，本规范只能作为通用运行约定，不能声明“完全适配”。
