# D-006｜RAG 框架与平台对比表

> 版本：v1.0
> 调研日期：2026-08-16
> 路线：开发框架（LangChain、LlamaIndex）与开箱平台（Dify、FastGPT、RAGFlow、MaxKB）
> 结论：本轮采用原生轻量编排，不新增上述运行时依赖。

## 1. 两条技术路线

- **开发框架**：以 Python/TypeScript 组件、对象和调用链为中心，便于嵌入现有代码、编写测试和自定义边界；团队需要自行承担部署、配置、观测与界面。
- **开箱平台**：以知识库、可视化工作流、模型配置、应用发布和管理界面为中心，上手和演示快；同时引入独立平台的数据模型、部署栈和升级治理。

本项目已经有 FastAPI、React、B/C/E 契约和三周交付边界。为保留 Citation 安全边界、C 的同进程评测和默认离线测试，直接写四个端口与一条显式服务链，比再引入框架或平台更短、更可审计。

## 2. 六项统一对比

| 方案 | 路线 | 核心抽象/能力 | 优点 | 代价与限制 | 本项目判断 |
|---|---|---|---|---|---|
| LangChain | 开发框架 | Document、loader、splitter、embedding、vector store、retriever；支持 2-step/agentic/hybrid RAG | 集成面广，组件替换与组合方便 | 抽象层较多，版本演进需要持续跟随；引用安全仍需业务层约束 | 适合更复杂编排；当前链路较短，不引入 |
| LlamaIndex | 开发框架 | 面向数据的 node/index/retriever/query engine/workflow | 数据摄取与索引概念完整，适合知识密集应用 | 需要适配现有 Pydantic 契约；旧 Query Pipeline 已 feature-freeze/deprecation，需使用 Workflows | 可作为未来复杂数据编排候选；当前不引入 |
| Dify | 开箱平台 | 模型管理、RAG、Agent、低代码 Workflow、API | 非开发成员可配置，应用发布与运维界面完整 | 形成独立平台依赖；现有代码、评测和 Citation 规则需要二次对接 | 适合快速运营型 AI 应用，不作为本 Demo 内核 |
| FastGPT | 开箱平台 | 知识库、引用式问答、节点工作流、Agent、OpenAI 兼容接口 | 中文资料与低代码使用体验友好，演示快 | 平台数据与工作流需要治理；自定义底层检索需遵循平台扩展方式 | 可做外部原型对照，不替换当前代码链 |
| RAGFlow | 开箱平台 | 深度文档理解、可干预切块、检索测试、端到端 RAG 与引用 | 对复杂 PDF/表格/版面更有针对性，可查看并修订 Chunk | 官方 Quickstart 的资源与 Docker 前提明显高于当前骨架；与 B 的既有解析职责重叠 | 若以后重点处理复杂资料可单独试点；本轮不引入 |
| MaxKB | 开箱平台 | 文档知识库、RAG、工作流、Agent、多路召回、模型管理 | 部署与中文管理界面完整，适合快速构建企业知识助手 | 同样引入平台数据模型与发布流程；深度代码级定制需额外集成 | 可用于低代码展示，不作为当前后端依赖 |

来源：[FW-LC1][FW-LC2][FW-LI1][FW-LI2][FW-DI1][FW-DI2][FW-FG1][FW-FG2][FW-RF1][FW-RF2][FW-MK1][FW-MK2][FW-MK3]。

## 3. 深度对比：LangChain 与 LlamaIndex

### 3.1 编排方式

LangChain 官方 Retrieval 文档把 loader、splitter、embedding、vector store、retriever 作为可替换模块，并给出 2-step、agentic、hybrid RAG 路线，适合围绕调用链和工具构建应用。[FW-LC1]

LlamaIndex 更强调“数据进入系统后如何成为可查询结构”，围绕 Node、Index、Retriever、Query Engine/Workflow 组织能力。需要注意：官方文档已将旧 Query Pipeline 标为 feature-freeze/deprecation，并建议转向 Workflows，因此不能按旧教程锁定架构。[FW-LI1]

### 3.2 数据结构和引用

- LangChain 常以 `Document(page_content, metadata)` 在 loader、splitter、retriever 间传递。
- LlamaIndex 常以 Node 及其 relationship/metadata 表达切块与来源关系。
- 两者都能保存 metadata，但“生成器不能直接构造资源名和页码、Citation 必须来自本次检索闭包”是本项目额外安全约束，不能只依赖框架默认回答格式。

### 3.3 扩展点和测试

- LangChain 的 retriever/vector store/runnable 生态适合快速接多供应商，但需要用版本锁定和集成测试控制行为漂移。
- LlamaIndex 的 ingestion/index/query 组件对复杂知识库更自然，但迁入本仓库会同时改变 B 的 Chunk 映射与 C 的评测调用方式。
- 当前原生端口只有 `EmbeddingProvider`、`VectorStore`、`Reranker`、`GroundedGenerator`；Fake 与离线实现可在不下载模型、不访问网络时测试，复杂度更符合本轮范围。

## 4. 平台路线简评

- Dify、FastGPT、MaxKB 都能较快形成知识库与工作流应用，适合运营人员参与配置。
- RAGFlow 在复杂格式解析、人工检查 Chunk 和引用方面更有针对性，但部署资源和组件也更重。[FW-RF1]
- 本项目已经由 B 负责解析/Chunk、C 负责评测、E 负责任务引擎；引入完整平台会出现职责重复和双数据源，因此本轮只保留技术调研结论。

## 5. 最终技术基线

采用“原生轻量编排 + 端口/适配器”：

```text
QaService / C Adapter
        ↓
     RagService
        ↓
Embedding → Qdrant → Reranker → GroundedGenerator → CitationAssembler
```

重新评估框架/平台的触发条件：链路出现复杂 DAG/Agent、需要大量现成 connector、非开发成员长期维护流程、或复杂文档解析成为主矛盾。届时必须用同一 C 评测集、Citation 闭包和默认无网络测试做迁移验收。

## 参考来源

来源 ID 与链接见 [research-sources.md](research-sources.md)。
