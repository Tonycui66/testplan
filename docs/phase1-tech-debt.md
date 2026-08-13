# Phase 1 技术债登记

以下问题在本轮 Phase 0 评审中标记为 low，允许延迟到 Phase 1 或对应模块实现时处理。

## 1. 前端 Axios 401 与路由守卫

- 来源：`frontend/src/api/client.ts`、`frontend/src/router/index.ts`
- 现状：当前仅有 Axios 请求拦截器，缺少 401 响应拦截、刷新/清理 token 逻辑；`/dashboard` 没有登录守卫。
- 计划：Phase 1 接入 IAM 后实现 401 重试、token 刷新、退出清理和 `router.beforeEach` 登录检查。

## 2. 后端配置、限流与公共依赖

- 来源：`backend/app/config.py`、`backend/app/middleware/rate_limit.py`、`backend/app/dependencies.py`
- 现状：配置使用标准 `dataclass`，限流为进程内 `defaultdict`，公共依赖尚未包含数据库会话和当前用户解析。
- 计划：Phase 1 切换到 `pydantic-settings`，限流迁移到 Redis 滑动窗口，并补齐 DB session、当前用户和 RBAC 公共依赖。
