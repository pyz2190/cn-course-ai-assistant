# 计算机网络 AI 助教项目骨架 Tasks

> 状态：v1.0，已审批（2026-07-28）  
> 依据：`spec.md` v1.0、`plan.md` v1.0

## 文件清单

| 操作 | 文件或目录 | 职责 |
|---|---|---|
| 新建 | 根配置与 `.github/` | 版本、统一命令、CI、PR 模板 |
| 新建 | `apps/api/` | FastAPI、领域模型、端口、Mock、路由、测试 |
| 新建 | `apps/web/` | React 界面、API 客户端、组件与测试 |
| 新建 | `contracts/`、`scripts/` | OpenAPI、JSON Schema、样例与一致性检查 |
| 新建 | `docs/`、`README.md`、`CONTRIBUTING.md` | 架构、角色、协作、接口变更和运行说明 |
| 修改 | `spec.md`、`plan.md`、`task.md`、`checklist.md` | 记录已审批状态与验收结果 |

## T1：建立仓库根基线

**文件：** `.editorconfig`、`.gitignore`、`.env.example`、`package.json`

**依赖：** 无

**步骤：**

1. 固定 Node、Python 与命令入口。
2. 配置前后端开发、契约生成、格式、检查、测试和构建脚本。
3. 忽略虚拟环境、依赖、构建结果、缓存、密钥和本地数据。
4. 提供无敏感信息的环境变量示例。

**验证：** 根配置可被 JSON/编辑器解析，`git diff --check` 无格式错误。

## T2：定义 API 领域模型

**文件：** `apps/api/app/domain/models.py`、`apps/api/app/domain/enums.py`

**依赖：** T1

**步骤：**

1. 实现 Plan 中的枚举与模型。
2. 增加页码范围、非空问题、置信度范围等校验。
3. 保持字段名与接口表一致。

**验证：** 合法 Fixture 校验通过，缺失必填字段或非法范围会产生校验错误。

## T3：定义端口与离线适配器

**文件：** `apps/api/app/services/ports.py`、`apps/api/app/services/qa.py`、`apps/api/app/adapters/mock.py`

**依赖：** T2

**步骤：**

1. 定义资料、检索、生成、任务和事件端口。
2. 实现 Mock 资料导入、检索和回答生成。
3. 实现内存任务仓库和事件接收器。
4. 保证模拟回答始终返回可定位引用。

**验证：** 服务单元测试在无网络、无密钥环境中通过。

## T4：实现 FastAPI 应用与路由

**文件：** `apps/api/app/main.py`、`apps/api/app/core/`、`apps/api/app/api/routes/`

**依赖：** T2、T3

**步骤：**

1. 提供 `create_app()`，配置 CORS、请求 ID 与异常处理。
2. 实现健康、资料、问答、任务和事件路由。
3. 为每个路由声明请求与响应模型。
4. 统一返回 `ApiError` 结构。

**验证：** TestClient 覆盖所有路由的成功与关键错误路径。

## T5：建立 API 测试与质量配置

**文件：** `apps/api/pyproject.toml`、`apps/api/tests/`

**依赖：** T2–T4

**步骤：**

1. 配置 FastAPI、Pydantic、pytest、httpx 和 Ruff。
2. 编写领域模型、服务和路由测试。
3. 覆盖引用、六类任务、事件记录和错误结构。

**验证：** `python -m pytest apps/api` 与 Ruff 检查通过。

## T6：导出共享契约

**文件：** `scripts/export_contracts.py`、`scripts/check_contracts.py`、`contracts/`

**依赖：** T2、T4

**步骤：**

1. 从 `create_app()` 导出格式稳定的 OpenAPI。
2. 导出 Chunk、知识点、引用、评测和任务 JSON Schema。
3. 提供合法与非法样例。
4. 编写重新生成并检测差异的检查脚本。

**验证：** 契约生成可重复；连续运行两次不会产生差异。

## T7：建立 React/Vite Web 工程

**文件：** `apps/web/package.json`、TypeScript 配置、`vite.config.ts`、`src/main.tsx`

**依赖：** T1

**步骤：**

1. 配置 React、TypeScript、Vite、Vitest、ESLint 和 Testing Library。
2. 设置开发代理与 `VITE_API_BASE_URL`。
3. 配置生成类型入口和测试环境。

**验证：** Web 类型检查和空应用生产构建通过。

## T8：实现 Web API 客户端

**文件：** `apps/web/src/api/`

**依赖：** T4、T6、T7

**步骤：**

1. 从 OpenAPI 生成 TypeScript 类型。
2. 实现统一请求函数和 `ApiError` 映射。
3. 实现健康、问答、任务和事件调用。

**验证：** Mock Fetch 测试覆盖成功响应和错误响应。

## T9：实现最小演示界面

**文件：** `apps/web/src/components/`、`apps/web/src/features/`、`apps/web/src/App.tsx`、样式文件

**依赖：** T7、T8

**步骤：**

1. 实现系统状态卡片。
2. 实现问答输入、加载、错误、回答和引用展示。
3. 实现任务列表、任务详情和六类标签。
4. 增加清晰的 Mock/独立系统提示。

**验证：** 组件测试覆盖状态、提问、引用和任务详情。

## T10：编写协作文档

**文件：** `README.md`、`CONTRIBUTING.md`、`docs/`、`.github/pull_request_template.md`

**依赖：** T1–T9

**步骤：**

1. 说明首次安装、启动、检查和常见问题。
2. 记录 A–E 角色与目录责任边界。
3. 记录分支、提交、PR 和接口变更流程。
4. 明确 Canvas 与真实模型均不在当前骨架中。

**验证：** 按 README 从空环境执行命令，无隐式步骤。

## T11：建立 CI

**文件：** `.github/workflows/ci.yml`

**依赖：** T5–T10

**步骤：**

1. 配置 Node 22 和 Python 3.11。
2. 安装前后端依赖。
3. 执行契约检查、Ruff、pytest、ESLint、类型检查、Vitest 和 Vite build。
4. 配置依赖缓存。

**验证：** 本地执行与 CI 等价的根检查命令通过。

## T12：端到端验收与发布准备

**文件：** `checklist.md`、Git 工作区

**依赖：** T1–T11

**步骤：**

1. 执行 `checklist.md` 全部检查。
2. 修复失败项并记录证据。
3. 检查差异只包含项目骨架。
4. 创建功能分支、提交、推送并准备 Draft PR。

**验证：** 全部本地检查通过；若远程权限不足，保留可推送提交并报告准确阻塞。

## 执行顺序

```text
T1 → T2 → T3 → T4 → T5
 │              └────→ T6
 └────→ T7 → T8 → T9
T5 + T6 + T9 → T10 → T11 → T12
```
