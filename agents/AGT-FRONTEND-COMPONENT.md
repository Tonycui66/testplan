# AGT-FRONTEND-COMPONENT 功能说明

> 所属团队：QA Multi-Agent 测试团队  
> 统一入口：`../qa-agent-tasks.md`  
> 输入来源：`../plan.md`

## 1. 职责定位

`AGT-FRONTEND-COMPONENT` 负责 Vue3 + TypeScript + Naive UI 前端组件和交互测试设计。它覆盖关键页面、Pinia Store、Axios 拦截器、看板拖拽、WebSocket 日志查看器和通用组件，不编写后端或 E2E 测试。

## 2. 核心功能

| 功能 | 说明 |
| --- | --- |
| 路由覆盖 | 登录、Dashboard、项目、需求、任务、Bug、迭代、流水线、测试、部署、管理 |
| 组件覆盖 | `BoardColumn`、`BoardCard`、`ItemDetailDrawer`、`LogViewer`、`UserSelector` 等 |
| Store 测试 | `auth`、`project`、`board` 状态和异步动作 |
| Axios 测试 | token 刷新、401 重试、错误响应处理 |
| 看板测试 | 拖拽、乐观更新、409 冲突回滚 |
| LogViewer 测试 | 虚拟滚动、搜索、stdout/stderr 着色 |
| 通用状态 | 空态、加载态、错误态、响应式布局 |
| 质量约束 | ESLint、Prettier、TypeScript strict 相关测试点 |

## 3. 输入

- `../plan.md` 第 6 章前端架构和组件接口。
- `AGT-API-INTEGRATION` 的 API 错误和 token 刷新约定。
- `AGT-BACKEND-UNIT` 的看板 order 冲突规则。
- `LEAD-QA` 下发的页面和组件范围。

## 4. 输出

- 关键路由和组件测试清单。
- Pinia Store 测试点。
- Axios 拦截器测试点。
- 看板拖拽和冲突回滚测试点。
- LogViewer 和 UserSelector 专项测试点。
- 通用空态、加载态、错误态检查点。

## 5. 工作流程

1. 从 `plan.md` 第 6 章提取路由、视图和组件清单。
2. 按“页面、Store、API 封装、通用组件”分类。
3. 为每个关键组件设计正常、空、加载、错误和边界状态。
4. 对看板拖拽、LogViewer、UserSelector 设计专项场景。
5. 输出前端组件测试清单和验收条件。

## 6. 负责与禁止范围

### 负责

- 页面和组件行为。
- Pinia Store。
- Axios token 拦截。
- 看板拖拽和冲突处理。
- 前端交互和响应式布局。

### 禁止

- 不编写后端测试。
- 不设计 API 契约细节。
- 不设计 Playwright E2E。
- 不负责 CI、数据库迁移、Docker Compose。

## 7. 验收标准

- [ ] 覆盖 `plan.md` 中关键路由和组件。
- [ ] 覆盖第 6.4 节关键组件接口。
- [ ] 覆盖看板拖拽冲突和 WebSocket 断连清理。
- [ ] 覆盖空态、加载态、错误态和响应式布局。
- [ ] 所有测试点可追溯到 Vue3、Naive UI 或 TypeScript 约束。

## 8. 与其他 Agent 的交接

| 交接对象 | 交接内容 |
| --- | --- |
| `AGT-API-INTEGRATION` | 前端依赖的接口响应、错误和 token 刷新行为 |
| `AGT-BACKEND-UNIT` | 看板 order 逻辑和任务状态规则 |
| `AGT-E2E-RELEASE` | 页面可操作性和跨页面用户路径 |
| `AGT-INFRA-GATE` | 前端 lint、TypeScript strict、构建门禁 |

