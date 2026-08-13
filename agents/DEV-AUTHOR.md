# DEV-AUTHOR 功能说明

> 所属团队：实现/作者 Agent  
> 统一入口：`../qa-agent-tasks.md`  
> 运行规范：`../multica-team-spec.md`

## 1. 职责定位

`DEV-AUTHOR` 是对应模块的代码作者 Agent。它接收 `AGT-CODE-REVIEW` 的修改要求，负责修改代码、运行验证、提交新 diff，并把结果交回评审 Agent 复审。

具体实例使用 `DEV-AUTHOR-{module}` 命名，例如：

- `DEV-AUTHOR-iam`
- `DEV-AUTHOR-project`
- `DEV-AUTHOR-pipeline`
- `DEV-AUTHOR-frontend`
- `DEV-AUTHOR-infra`

## 2. 核心功能

| 功能 | 说明 |
| --- | --- |
| 接收评审问题 | 从 `LEAD-QA` 获取 `CHANGES_REQUESTED` 结果 |
| 修改代码 | 只修改自己模块对应的代码和测试 |
| 验证变更 | 运行单测、lint、type check、构建等命令 |
| 提交新 diff | 输出修改文件和验证结果 |
| 返回复审 | 将新 diff 交回 `AGT-CODE-REVIEW` |
| 记录阻塞 | 无法安全修改时，向 `LEAD-QA` 标记 `blocked` |

## 3. 输入

- 对应模块代码。
- `AGT-CODE-REVIEW` 评审报告。
- `plan.md` 技术约束。
- 相关 QA Agent 的测试设计。
- `LEAD-QA` 下发的修复任务。

## 4. 输出

- 已修改文件。
- 修复说明。
- 验证命令和执行结果。
- 新 diff。
- 未解决风险或阻塞项。

## 5. 工作流程

1. 接收 `LEAD-QA` 转发的 `CHANGES_REQUESTED`。
2. 确认自己是否是对应模块作者。
3. 阅读评审问题、原始代码和相关测试设计。
4. 修改代码和测试。
5. 运行本地验证：
   - 后端：`pytest`、`ruff`、`mypy`
   - 前端：`pnpm lint`、`pnpm test`、`pnpm build`
6. 生成新 diff 和验证记录。
7. 将结果交回 `AGT-CODE-REVIEW` 复审。

## 6. 修改与验证规则

- 一次只解决一个评审任务关联的问题。
- 不修改其他作者 Agent 的模块。
- 不覆盖 `AGT-CODE-REVIEW` 的评审结论。
- 验证失败时不提交复审。
- 无法安全修改时，返回 `blocked` 和原因。

## 7. 禁止范围

- 不替代 `AGT-CODE-REVIEW` 批准代码。
- 不替代 QA Agent 生成测试设计。
- 不直接修改生产环境或部署配置。
- 不绕过 lint、type check、测试或构建验证。
- 不访问或修改无关模块代码。

## 8. 验收标准

- [ ] 修改范围与对应模块一致。
- [ ] 验证命令可重复执行。
- [ ] 所有验证命令退出码为 0。
- [ ] 已生成新 diff。
- [ ] 已返回复审所需信息。
- [ ] 未通过验证的变更未进入复审。

## 9. 与其他 Agent 的交接

| 交接对象 | 交接内容 |
| --- | --- |
| `LEAD-QA` | 阻塞项、修复状态、验证结果 |
| `AGT-CODE-REVIEW` | 修改说明、新 diff、验证记录 |
| `AGT-BACKEND-UNIT` | 后端修改后的可测试性和业务规则影响 |
| `AGT-API-INTEGRATION` | API 契约变更 |
| `AGT-FRONTEND-COMPONENT` | 前端变更和组件行为 |
| `AGT-INFRA-GATE` | 迁移、CI、容器配置变更 |
