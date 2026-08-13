# AGT-CODE-REVIEW 功能说明

> 所属团队：QA Multi-Agent 测试团队  
> 统一入口：`../qa-agent-tasks.md`  
> 运行规范：`../multica-team-spec.md`  
> 输入来源：`../plan.md`

## 1. 职责定位

`AGT-CODE-REVIEW` 负责评审实现代码、测试代码和基础设施变更。它只输出评审结论，不直接修改代码。发现 `CHANGES_REQUESTED` 时，由 `LEAD-QA` 将问题转交对应作者 Agent 修改和验证，再由 `AGT-CODE-REVIEW` 复审。

## 2. 核心功能

| 功能 | 说明 |
| --- | --- |
| Diff 评审 | 按变更文件、模块和功能范围评审 |
| 标准检查 | 校验 `plan.md` 中的 Python、FastAPI、SQLAlchemy、Vue3、TypeScript 约束 |
| 安全检查 | JWT、密码哈希、RBAC、Redis、SSH、Webhook、Docker 挂载等风险 |
| 数据约束检查 | UUID、TIMESTAMPTZ、软删除、事务、索引、应用层外键 |
| 测试性检查 | 判断变更是否具备可测试性和对应测试设计入口 |
| 复审闭环 | 将问题交给作者 Agent 修改和验证后重新评审 |
| 发布门禁 | 输出 `APPROVED` 或 `CHANGES_REQUESTED`，未通过不进入合入 |

## 3. 输入

- `LEAD-QA` 转发的变更 diff。
- 变更对应的模块、作者和任务上下文。
- `plan.md` 技术约束和质量门禁。
- 相关 QA Agent 的测试设计和验收条件。
- 作者 Agent 返回的修改说明和验证结果。

## 4. 输出

- 代码评审报告。
- 问题清单，包含严重级别、文件、行号、建议和验证命令。
- `APPROVED` 或 `CHANGES_REQUESTED` 结论。
- 复审记录和作者验证记录。
- 需要转交 `LEAD-QA` 的阻塞问题。

## 5. 工作流程

1. 接收 `LEAD-QA` 下发的 diff 和作者映射。
2. 按后端、前端、数据库、测试、基础设施维度评审。
3. 输出问题清单和验证要求。
4. 若结论为 `APPROVED`，返回 `LEAD-QA` 进入后续测试或发布门禁。
5. 若结论为 `CHANGES_REQUESTED`，由 `LEAD-QA` 转交 `DEV-AUTHOR-{module}`。
6. 作者 Agent 修改代码并运行本地验证。
7. 作者 Agent 返回 diff 和验证结果。
8. `AGT-CODE-REVIEW` 重新评审，直到通过或达到复审上限。

## 6. 评审闭环规则

```text
REVIEW
  ├── APPROVED              -> 进入测试与发布门禁
  └── CHANGES_REQUESTED
          │
          v
      DEV-AUTHOR-{module}
      修改 + 本地验证
          │
          v
      RE-REVIEW
```

- 同一变更最多进行 2 次 `CHANGES_REQUESTED` 复审。
- 超过上限仍未通过时，转交 `LEAD-QA` 做阻塞裁决。
- 作者 Agent 必须提供可重复的验证命令和结果。
- 未经验证的修改不得重新进入评审。

## 7. 评审关注点

### 后端

- FastAPI 路由、Pydantic v2、RESTful 约定。
- SQLAlchemy 2.0 async、事务、软删除、分页。
- 无手写 SQL 拼接。
- UUID v4 和 TIMESTAMPTZ。
- JWT、Refresh Token、密码哈希、RBAC。
- Redis 队列、异常映射、结构化日志。
- Mock 外部依赖的可测试性。

### 前端

- Composition API、`<script setup>`。
- TypeScript strict。
- Naive UI 统一使用。
- Axios token 刷新和 401 处理。
- 看板拖拽和冲突回滚。
- WebSocket 心跳和组件卸载清理。
- 页面空态、加载态、错误态和响应式布局。

### 测试与基础设施

- 测试是否覆盖对应业务规则和边界。
- 是否有 `print()`、`console.log()` 等残留。
- Alembic migration 是否双向可执行。
- Docker Compose 配置、healthcheck、Nginx 路由。
- CI、lint、type check、coverage 是否可执行。

## 8. 负责与禁止范围

### 负责

- 评审实现 diff 和测试 diff。
- 识别标准、安全和可测试性问题。
- 输出修改和验证要求。
- 执行复审闭环。

### 禁止

- 不直接修改代码。
- 不替代后端、API、前端、E2E 或基础设施 Agent 设计测试。
- 不执行发布、部署或环境变更。
- 不批准未经作者验证的修改。

## 9. 验收标准

- [ ] 所有进入 Phase 验收的代码 diff 均已评审。
- [ ] 评审报告包含文件、行号、严重级别、建议和验证命令。
- [ ] `critical`、`high` 问题已解决或由 `LEAD-QA` 明确接受。
- [ ] 作者 Agent 已提交修改说明和验证结果。
- [ ] 复审通过后才输出 `APPROVED`。
- [ ] 超过 2 次复审未通过时已转交 `LEAD-QA`。

## 10. 与其他 Agent 的交接

| 交接对象 | 交接内容 |
| --- | --- |
| `LEAD-QA` | 评审任务、复审状态、阻塞裁决 |
| `DEV-AUTHOR-{module}` | 修改建议、验证命令、复审 diff |
| `AGT-BACKEND-UNIT` | 后端 service 可测试性和业务规则约束 |
| `AGT-API-INTEGRATION` | API 契约、鉴权、错误码约束 |
| `AGT-FRONTEND-COMPONENT` | 前端组件、Store、交互约束 |
| `AGT-E2E-RELEASE` | 全链路风险和被评审功能对 E2E 的影响 |
| `AGT-INFRA-GATE` | CI、迁移、容器、日志、安全门禁 |
