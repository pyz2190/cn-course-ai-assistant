# 计算机网络 AI 助教

面向《计算机网络》课程的 AI 助教原型。仓库提供一套可直接联调的前后端骨架、稳定的数据契约和本地 Mock，使五位成员可以在 Canvas 接口尚未开放的情况下并行开发。

当前骨架包含：

- React + TypeScript + Vite 学生端工作台
- FastAPI + Pydantic 后端 API
- 课程资料导入、引用式问答、六类教学任务、学习事件接口
- RAG、模型、资源导入和任务存储的可替换端口
- OpenAPI 与 JSON Schema 契约自动生成
- 前后端单元测试、静态检查和 GitHub Actions

## 快速开始

环境要求：

- Node.js 22 或更高版本
- Python 3.11 或更高版本

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "apps/api[dev]"
npm install
npm run contracts
npm run dev
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e "apps/api[dev]"
npm install
npm run contracts
npm run dev
```

启动后访问：

- 学生端：<http://127.0.0.1:5173>
- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

当前 API 使用内存 Mock，不需要数据库、向量库或模型密钥。复制 `.env.example` 为 `.env` 后可调整本地配置。

## 常用命令

```bash
npm run dev              # 同时启动前后端
npm run contracts        # 生成 OpenAPI、JSON Schema 和前端类型
npm run test             # 运行前后端测试
npm run lint             # 运行 Ruff 和 ESLint
npm run typecheck        # TypeScript 类型检查
npm run build            # 构建前端
npm run check            # 执行提交前完整检查
```

## 项目结构

```text
apps/
  api/                    FastAPI 服务、领域模型、端口与 Mock 适配器
  web/                    React 学生端
contracts/
  examples/               组员联调样例
  schemas/                自动生成的 JSON Schema
docs/                     架构、分工和协作规范
scripts/                  契约生成与漂移检查
spec.md                   已确认需求
plan.md                   已确认技术方案
task.md                   已确认开发任务
checklist.md              已确认验收清单
```

## 协作入口

开始开发前先阅读：

1. [分工边界](docs/roles.md)
2. [架构与扩展点](docs/architecture.md)
3. [协作规范](docs/collaboration.md)
4. [接口变更流程](docs/interface-change.md)

Canvas 当前不作为系统运行依赖。未来获得 API、LTI 或课程导出权限后，只需实现资源导入适配器，不应把 Canvas 专有字段泄漏到领域模型和前端。
