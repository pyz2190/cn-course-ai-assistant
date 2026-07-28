# 计算机网络 AI 助教项目骨架 Plan

> 状态：v1.0，已审批（2026-07-28）
> 依据：`spec.md` v1.0

## 架构概览

仓库采用前后端分离的单仓库结构：

- Web：React + TypeScript + Vite，负责服务状态、模拟问答、引用展示和任务浏览。
- API：FastAPI + Pydantic，负责稳定的 HTTP 契约、数据校验、模拟服务和 OpenAPI 输出。
- Contracts：由 API 的 Pydantic 模型导出 OpenAPI 与 JSON Schema，再生成 Web 使用的 TypeScript 类型，避免双份字段定义。
- Adapters：真实模型、Embedding、Reranker 和向量存储均通过端口隔离；默认只注册离线 Mock。
- Quality：根目录提供统一开发命令，CI 分别验证 Python 与 TypeScript，并检查契约是否同步。

默认链路不依赖 Canvas、数据库、模型 API 或向量数据库。

## 核心数据结构

### `ChunkMetadata`

字段：

- `chunk_id: str`
- `resource_id: str`
- `knowledge_point_ids: list[str]`
- `title: str`
- `content: str`
- `chapter: str`
- `page_start: int | None`
- `page_end: int | None`
- `language: Language`
- `content_type: ContentType`
- `source_url: str | None`
- `version: str`
- `access_level: AccessLevel`
- `parse_status: ParseStatus`
- `updated_at: datetime`

### `KnowledgePoint`

字段：

- `knowledge_point_id: str`
- `name: str`
- `chapter: str`
- `parent_id: str | None`
- `kind: str`
- `difficulty: Difficulty`
- `keywords_zh: list[str]`
- `keywords_en: list[str]`
- `prerequisite_ids: list[str]`
- `summary: str`
- `review_status: ReviewStatus`
- `maintainer: str`

### `Citation`

字段：

- `citation_id: str`
- `chunk_id: str`
- `resource_id: str`
- `title: str`
- `chapter: str`
- `page_start: int | None`
- `page_end: int | None`
- `quote: str`
- `source_url: str | None`

### `ResourceImportRequest` / `ResourceImportResponse`

- 请求：`course_id`、`resource_type`、`title`、`version`、`language`、`content_type`、`source_url`
- 响应：`resource_id`、`sync_status`、`metadata`、`error`

### `AskRequest` / `AskResponse`

- 请求：`course_id`、`user_id`、`question`
- 响应：`answer`、`citations`、`confidence`、`request_id`

### `TaskTemplate`

字段：

- `task_id: str`
- `title: str`
- `description: str`
- `task_type: TaskType`
- `knowledge_point_ids: list[str]`
- `resource_ids: list[str]`
- `prerequisite_ids: list[str]`
- `completion_criteria: list[str]`
- `ai_feedback_points: list[str]`
- `status: TaskStatus`

`TaskType` 固定为六类：基础学习、协议分析与仿真、案例分析、创新挑战、项目实践、排错。

### `LearningEvent`

字段：

- `event_id: str`
- `course_id: str`
- `user_id: str`
- `event_type: EventType`
- `object_id: str`
- `occurred_at: datetime`
- `payload: dict[str, JsonValue]`

### `EvaluationItem`

字段：

- `evaluation_id: str`
- `question: str`
- `expected_answer: str`
- `category: QuestionCategory`
- `difficulty: Difficulty`
- `knowledge_point_ids: list[str]`
- `scoring_dimensions: list[ScoringDimension]`

### `ApiError`

字段：

- `code: str`
- `message: str`
- `request_id: str`
- `details: dict[str, JsonValue] | None`

## 模块设计

### API 入口

职责：创建 FastAPI 应用、挂载中间件、异常处理器和版本化路由。

公开入口：

- `create_app() -> FastAPI`
- `GET /api/v1/health`
- `POST /api/v1/resources/import`
- `POST /api/v1/qa/ask`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `POST /api/v1/events`

### 资料模块

职责：接收内部资料导入请求，生成符合契约的模拟资源和 Chunk Metadata。

端口：

- `ResourceImporter.import_resource(request) -> ResourceImportResponse`

默认实现：`MockResourceImporter`

### RAG 问答模块

职责：组合检索与回答生成，确保回答携带引用。

端口：

- `Retriever.retrieve(question, course_id) -> list[ChunkMetadata]`
- `AnswerGenerator.generate(question, chunks) -> AskResponse`
- `QaService.ask(request) -> AskResponse`

默认实现：`MockRetriever`、`MockAnswerGenerator`

### 任务模块

职责：读取六类任务的示例数据并提供列表与详情。

端口：

- `TaskRepository.list_tasks() -> list[TaskTemplate]`
- `TaskRepository.get_task(task_id) -> TaskTemplate | None`

默认实现：`InMemoryTaskRepository`

### 学习行为模块

职责：校验并接收独立系统内部事件，不连接 Canvas。

端口：

- `EventSink.record(event) -> LearningEvent`

默认实现：`InMemoryEventSink`

### Web API 客户端

职责：集中处理基础地址、请求、错误映射和生成类型；UI 组件不得散落拼接 URL。

公开入口：

- `getHealth()`
- `askQuestion(request)`
- `listTasks()`
- `getTask(taskId)`
- `recordEvent(event)`

### Web 界面

职责：

- `SystemStatus`：展示 API 连接状态。
- `ChatPanel`：提交问题、展示模拟回答、置信度和引用。
- `TaskList`：展示任务卡片。
- `TaskDetail`：展示知识点、资源、完成判据和 AI 反馈介入点。

## 模块交互

### 问答链路

1. Web 提交 `AskRequest`。
2. API 路由调用 `QaService`。
3. `QaService` 调用 `Retriever` 获取 Chunk。
4. `AnswerGenerator` 基于 Chunk 生成模拟回答和 `Citation`。
5. API 返回 `AskResponse`。
6. Web 展示回答，并按引用定位资源、章节和页码。

### 资料导入链路

1. 调用方提交 `ResourceImportRequest`。
2. `ResourceImporter` 生成资源标识和模拟 Chunk Metadata。
3. API 返回同步状态；不访问 Canvas。

### 任务链路

1. Web 读取任务列表。
2. 选择任务后读取详情。
3. UI 展示完成判据和 AI 反馈介入点。
4. 示例交互可向事件接口记录 `LearningEvent`。

### 契约生成链路

1. Pydantic 模型定义 API 与领域结构。
2. 脚本从 FastAPI 应用导出 `contracts/openapi.json`。
3. 脚本导出关键模型的 JSON Schema。
4. `openapi-typescript` 生成 Web 类型。
5. CI 重新生成后检查 Git 工作区无差异。

## 文件组织

```text
cn-course-ai-assistant/
├── .github/
│   ├── pull_request_template.md
│   └── workflows/ci.yml
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── adapters/
│   │   │   ├── api/routes/
│   │   │   ├── core/
│   │   │   ├── domain/
│   │   │   ├── services/
│   │   │   └── main.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── web/
│       ├── src/
│       │   ├── api/
│       │   ├── components/
│       │   ├── features/
│       │   └── test/
│       ├── package.json
│       └── vite.config.ts
├── contracts/
│   ├── examples/
│   ├── schemas/
│   └── openapi.json
├── docs/
│   ├── architecture.md
│   ├── collaboration.md
│   ├── interface-change.md
│   └── roles.md
├── scripts/
│   ├── export_contracts.py
│   └── check_contracts.py
├── .editorconfig
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── README.md
├── package.json
├── checklist.md
├── plan.md
├── spec.md
└── task.md
```

## 技术决策

| 决策点 | 选择 | 理由 |
|---|---|---|
| 工程形态 | 单仓库、前后端分离 | 五人共享契约，同时允许模块独立开发 |
| Web | React + TypeScript + Vite | 组件边界清晰、构建快速、适合 Demo |
| API | FastAPI + Pydantic | 自动校验与 OpenAPI 适合接口先行 |
| Python 版本 | 3.11+ | 类型能力稳定，团队环境易获得 |
| Node 版本 | 22 LTS | 满足当前 Vite 工具链要求 |
| 契约源 | Pydantic/OpenAPI | 由后端生成前端类型，避免字段漂移 |
| 默认存储 | 内存与版本化 Fixture | 离线可复现，不提前绑定数据库 |
| 模型与向量库 | Protocol + Mock Adapter | D 尚未定最终选型，骨架保持可替换 |
| Web 数据获取 | 轻量 API Client + React 状态 | 骨架规模小，暂不引入额外服务端状态库 |
| 样式 | 原生 CSS 变量与组件样式 | 降低依赖，方便 E 后续替换 |
| 测试 | pytest + TestClient；Vitest + Testing Library | 分别覆盖 API 和可观察 UI 行为 |
| 质量工具 | Ruff；ESLint；TypeScript；Vite build | 提供快速、统一的本地与 CI 入口 |

## Spec 覆盖

- F1、F8：由单仓库和模块目录覆盖。
- F2、F9：由最小 Web、API、Fixture 与开发命令覆盖。
- F3–F7：由版本化路由、Pydantic 模型和服务端口覆盖。
- F10：由 Protocol 与 Mock Adapter 覆盖。
- F11：由 README、CONTRIBUTING 和 docs 覆盖。
- F12：由根命令与 GitHub Actions 覆盖。
