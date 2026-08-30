# 计算机网络 AI 助教

面向《计算机网络》课程的 AI 助教与教学任务引擎原型。系统完全独立运行，不依赖 Canvas 的身份、资源、成绩或学习行为接口。

**默认离线运行**：不需要 GPU、数据库、模型密钥或联网。首次装好依赖后即可启动完整演示。

当前能力：

- React + TypeScript + Vite 前端，含学生端工作台与教师／助教工作台，可在界面顶部切换
- FastAPI + Pydantic 后端，统一错误结构与 OpenAPI 契约
- 课程资料上传解析（PDF / PPT / 字幕 / RFC / 文本 / Markdown）并自动切块入库
- Qdrant 向量检索 + 可选重排 + 按句挂角标的可追溯引用
- 中英双语语料，中文问题召回中文语料，英文问题召回英文语料
- 六类教学任务模板，含知识点、资料、完成判据与 AI 反馈介入点，支持草稿与发布状态流转
- 课程知识点与知识图谱（先修关系、章节层次）
- 人工反馈闭环：学生反馈 → 教师审核 → 知识库变更任务 → 关闭，全流程有界面
- 学习行为事件记录与查询、语料质量审查接口
- 契约自动生成（OpenAPI → JSON Schema → 前端 TypeScript 类型）
- 前后端测试、静态检查与 GitHub Actions

---

## 一、运行环境要求

| 项目 | 要求 | 说明 |
|---|---|---|
| **Node.js** | 22 或更高 | 前端构建与工作区管理，Vite 工具链要求 |
| **Python** | 3.11 或更高 | 后端 API，依赖 3.11+ 的类型语法 |
| **npm** | 随 Node 22 附带 | 使用 workspaces，勿用 yarn/pnpm 混装 |
| 操作系统 | Windows / macOS / Linux | 均已验证 |
| 磁盘 | 约 1.5 GB | 主要是 node_modules 与 Python 依赖 |
| 网络 | 仅安装依赖时需要 | 装完后运行、测试、演示全程离线 |

**不需要**：GPU、CUDA、Docker、外部数据库、向量数据库服务、大模型 API Key、Canvas 账号或校园网权限。

检查版本：

```bash
node -v      # 应 >= v22
python --version   # 应 >= 3.11（Windows 上可能是 python，Linux/macOS 上可能是 python3）
```

---

## 二、启动项目

### 1. 获取代码

```bash
git clone https://github.com/pyz2190/cn-course-ai-assistant.git
cd cn-course-ai-assistant
```

### 2. 创建虚拟环境并安装依赖

**Windows PowerShell：**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "apps/api[dev]"
npm install
```

**macOS / Linux：**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "apps/api[dev]"
npm install
```

> 虚拟环境需要保持激活状态，后端命令都在其中执行。新开终端记得重新 activate。

### 3. 生成契约与前端类型

```bash
npm run contracts
```

这一步从后端 Pydantic 模型导出 `contracts/openapi.json` 和 JSON Schema，再生成前端 TypeScript 类型。**首次启动必须执行**，否则前端类型缺失导致编译失败。

### 4. 启动前后端

```bash
npm run dev
```

该命令通过 `concurrently` 同时拉起两个服务：

| 服务 | 地址 | 说明 |
|---|---|---|
| 学生端 | http://127.0.0.1:5173 | Vite 开发服务器，热更新 |
| 后端 API | http://127.0.0.1:8000 | Uvicorn，代码改动自动重载 |

前端通过 Vite 代理把 `/api` 转发到 `127.0.0.1:8000`，因此本地开发无需配置跨域。

也可以分开启动，便于单独调试：

```bash
npm run dev:api    # 只启动后端
npm run dev:web    # 只启动前端
```

### 5. 验证启动成功

浏览器打开 <http://127.0.0.1:5173>，页面右上角应显示 API 在线状态。然后：

1. 点击任一推荐问题（如「TCP 为什么需要三次握手？」）
2. 应返回带 `[1]` 角标的回答，下方列出引用来源（书名、章节、页码）
3. 向下滚动，任务区应显示六类教学任务，点击可查看详情
4. 点击顶部「教师 / 助教视图」，可进入工作台查看反馈审核、知识库变更、资料上传与学习行为四个模块

命令行验证：

```bash
curl http://127.0.0.1:8000/api/v1/health
# {"status":"ok","service":"cn-course-ai-assistant-api","mode":"offline"}
```

其他入口：

- 交互式 API 文档（Swagger）：<http://127.0.0.1:8000/docs>
- OpenAPI 规格：<http://127.0.0.1:8000/openapi.json>

---

## 三、安装或启动失败时

**`pysrt` 安装报错 `AttributeError: install_layout`**
部分 Linux 发行版自带的 setuptools 被打过补丁，与源码包构建不兼容。在虚拟环境内升级构建工具后重装：

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "apps/api[dev]"
```

**`ModuleNotFoundError: No module named 'app'`**
虚拟环境没激活，或没有执行 `pip install -e "apps/api[dev]"`。确认命令行提示符前有 `(.venv)`。

**前端报类型错误 / 找不到 `./schema`**
没有执行 `npm run contracts`。补跑一次即可。

**端口被占用**
后端改端口：`python -m uvicorn app.main:app --app-dir apps/api --reload --port 8001`；
前端改端口在 `apps/web/vite.config.ts` 的 `server.port`，同时需相应调整 `proxy.target`。

**上传文件返回 422**
文件扩展名与 `content_type` 不匹配。对应关系见下方「资料上传」。

---

## 四、常用命令

```bash
npm run dev              # 同时启动前后端
npm run dev:api          # 仅后端
npm run dev:web          # 仅前端

npm run contracts        # 生成 OpenAPI、JSON Schema 与前端类型
npm run check:contracts  # 校验契约是否与代码同步（CI 会卡这一步）

npm run test             # 前后端全部测试
npm run test:api         # 后端 pytest
npm run test:web         # 前端 Vitest

npm run lint:api         # Ruff 静态检查
npm run lint:web         # ESLint
npm run typecheck:web    # TypeScript 类型检查
npm run format:api       # Ruff 格式化

npm run build            # 构建前端产物到 apps/web/dist
npm run rag:benchmark    # 本地 RAG 基准（10 个示例 Chunk）

npm run check            # 提交前完整检查，等价于 CI
```

`npm run check` 会依次执行依赖漏洞审计、契约同步校验、Ruff、pytest、ESLint、TypeScript 检查、Vitest 和生产构建。**提交前请确保这条命令通过。**

---

## 五、接口一览

所有接口以 `/api/v1` 为前缀。

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/health` | 健康检查与当前运行模式 |
| `POST` | `/qa/ask` | 课程问答，返回回答、置信度与可追溯引用 |
| `POST` | `/resources/import` | 资料导入契约（登记元数据） |
| `POST` | `/resources/upload` | 上传课程文件，自动解析、切块、向量化入库 |
| `GET` | `/resources` | 已导入资料列表，可按 `course_id` 过滤 |
| `GET` | `/resources/{resource_id}/chunks` | 读取某份资料解析出的全部 Chunk |
| `GET` | `/knowledge-points` | 课程知识点列表，可按 `chapter`、`parent_id` 浏览知识图谱 |
| `GET` | `/knowledge-points/{knowledge_point_id}` | 知识点详情，含先修关系 |
| `GET` | `/tasks` | 教学任务列表，可按 `status`、`task_type` 过滤 |
| `POST` | `/tasks` | 发布教学任务，可传 `status=draft` 先存草稿 |
| `GET` | `/tasks/{task_id}` | 任务详情 |
| `PATCH` | `/tasks/{task_id}/status` | 任务状态流转（草稿／已发布／已完成） |
| `POST` | `/events` | 记录学习行为事件 |
| `GET` | `/events` | 查询学习行为事件，可按课程、学生、类型、对象过滤 |
| `POST` | `/feedback` | 学生提交回答反馈 |
| `GET` | `/feedback` | 教师与助教的待审核队列 |
| `GET` | `/feedback/{feedback_id}` | 单条反馈详情 |
| `PATCH` | `/feedback/{feedback_id}/review` | 审核反馈；通过时自动生成知识库变更任务 |
| `GET` | `/knowledge-base/changes` | 知识库变更任务列表 |
| `GET` | `/knowledge-base/changes/{change_id}` | 变更任务详情 |
| `PATCH` | `/knowledge-base/changes/{change_id}` | 推进或关闭变更任务 |
| `POST` | `/quality/reviews` | 提交语料质量审查记录 |
| `GET` | `/quality/reviews` | 查询质量审查记录，可按 `chunk_id` 过滤 |
| `GET` | `/quality/reviews/{review_id}` | 单条质量审查记录 |

完整字段定义见 <http://127.0.0.1:8000/docs>。

### 人工反馈闭环

学生对回答提交反馈后，教师或助教在 `/feedback` 队列中审核；判定为无效回答时会自动生成一条知识库变更任务，处理完成后通过 `PATCH /knowledge-base/changes/{change_id}` 关闭，形成「反馈 → 审核 → 优化知识库」的闭环。

该流程在界面上对应顶部的「教师 / 助教视图」，包含四个模块：

| 模块 | 作用 |
|---|---|
| 反馈审核 | 待审核队列，逐条判定并给出后续处理建议 |
| 知识库变更 | 审核通过后自动生成的变更任务列表 |
| 资料上传 | 上传课程文件并查看解析、切块与入库结果 |
| 学习行为 | 按课程、学生、类型、对象查询学习事件 |

### 资料上传

`POST /api/v1/resources/upload` 使用 `multipart/form-data`，字段为 `file`、`course_id`、`title`、`content_type`、`language`、`version`、`knowledge_point_ids`。

支持的文件类型：

| `content_type` | 允许扩展名 |
|---|---|
| `pdf` | `.pdf` |
| `ppt` | `.pptx` `.ppt` |
| `subtitle` | `.srt` `.vtt` |
| `rfc` / `text` / `other` | `.txt` `.md` |

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/resources/upload \
  -F "file=@lecture.srt" \
  -F "course_id=computer-networks" \
  -F "title=运输层讲解" \
  -F "content_type=subtitle" \
  -F "language=zh" \
  -F "knowledge_point_ids=kp-transport-tcp-handshake"
```

### 课程问答

```bash
curl -X POST http://127.0.0.1:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"course_id":"computer-networks","user_id":"student-demo","question":"TCP 为什么需要三次握手？"}'
```

响应包含 `answer`（句末带 `[n]` 角标）、`citations`（资源、章节、页码、原文摘录）、`confidence`、`request_id`、`degraded` 与 `mode`。

---

## 六、配置说明

默认配置无需修改即可运行。需要调整时，复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

常用配置项：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CN_AI_MODE` | `offline` | `offline` 全离线；`external` 接外部模型 |
| `CN_AI_VECTOR_STORE` | `memory` | `memory` 内存；`local` 本地持久化；`remote` 远程 Qdrant |
| `CN_AI_QDRANT_PATH` | `.data/qdrant` | 本地持久化路径，`local` 模式生效 |
| `CN_AI_EMBEDDING_PROVIDER` | `offline` | 改为 `bge` 需安装 `apps/api[models]` 并下载权重 |
| `CN_AI_RERANKER_ENABLED` | `true` | 是否启用重排 |
| `CN_AI_TOP_K` | `3` | 最终送入生成的 Chunk 数 |
| `CN_AI_FETCH_K` | `8` | 向量召回候选数 |
| `CN_AI_MIN_RETRIEVAL_SCORE` | `0.10` | 低于该分数的候选被丢弃 |
| `CN_AI_ALLOW_DEGRADED` | `true` | 组件不可用时是否降级而非报错 |
| `CN_AI_CORS_ORIGINS` | 本地 5173 | 允许的浏览器来源 |
| `VITE_API_BASE_URL` | 空 | 留空则走 Vite 的 `/api` 代理 |

切换到外部模型需同时设置 `CN_AI_MODE=external`、`CN_AI_GENERATOR_PROVIDER=openai-compatible` 和 `CN_AI_MODEL_BASE_URL`，否则启动时配置校验会直接报错。

可选安装本地 BGE 模型依赖（默认测试不需要，也不会下载权重）：

```bash
python -m pip install -e "apps/api[models]"
```

---

## 七、评测

评测通过同进程适配器调用与线上相同的 `RagService`，不会把标准答案或标注要点泄漏给生成链路。

```bash
python scripts/evaluate.py --adapter rag --dry-run   # 校验执行计划，不调用模型
python scripts/run_evaluation_pipeline.py validate   # 校验评测数据
```

完整流程（数据校验 → 同步正式集 → 执行 → 人工打分 → 生成基线报告）见 [`evaluation/README.md`](evaluation/README.md)。

---

## 八、项目结构

```text
apps/
  api/                    FastAPI 服务
    app/
      adapters/           Mock 与真实适配器（文档解析、RAG、评测）
      api/routes/         版本化路由
      core/               配置、依赖注入、错误处理
      domain/             领域模型与枚举（契约单一事实来源）
      services/           端口定义与 RAG、问答服务
    tests/                后端测试
  web/                    React 学生端
    src/
      api/                API 客户端与自动生成的类型
      components/         通用组件
      features/           问答面板、任务工作台
contracts/                OpenAPI、JSON Schema 与联调样例
docs/                     架构、分工、协作规范与各角色交付文档
evaluation/               问答库、标注、评分规则与评测流水线
scripts/                  契约生成、漂移检查与评测脚本
```

---

## 九、协作入口

开始开发前请阅读：

1. [分工边界](docs/roles.md)
2. [架构与扩展点](docs/architecture.md)
3. [协作规范](docs/collaboration.md)
4. [接口变更流程](docs/interface-change.md)

**接口变更必须先改契约、再改实现**：修改 `apps/api/app/domain/models.py` 后运行 `npm run contracts` 重新生成，并提交生成结果，否则 CI 的 `check:contracts` 会失败。

各角色交付文档：

- `docs/D-008-任务引擎设计方案.md`：任务引擎与六类教学任务
- `docs/D-010-Demo运行说明.md`：Demo 演示说明与截图
- `docs/d-rag/D-004` ～ `D-007`：RAG 技术方案、向量库与框架对比、微调与部署分析

---

## 十、项目边界

系统不接入 Canvas API、LTI、课程身份、资源同步、成绩回写或学习行为回写。任务数据与学习行为记录完全由本系统承载。

未来获得 Canvas API、LTI 或课程导出权限后，只需实现资源导入适配器即可接入，不应把 Canvas 专有字段泄漏到领域模型和前端。
