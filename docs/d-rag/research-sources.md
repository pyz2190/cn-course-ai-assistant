# D｜RAG 与模型技术调研来源登记

> 调研日期：2026-08-16  
> 使用规则：交付文档中的事实优先引用官方文档、官方仓库、模型卡或原始论文；未在本项目复现的内容标为“官方声明”或“分析推断”。

## 向量数据库

| ID | 来源 | 用途 |
|---|---|---|
| DB-C1 | [Chroma：Manage Collections](https://docs.trychroma.com/docs/collections/manage-collections) | collection、embedding function、collection metadata |
| DB-C2 | [Chroma：Query and Get](https://docs.trychroma.com/docs/querying-collections/query-and-get) | 向量查询、metadata/document filter |
| DB-C3 | [Chroma 官方仓库](https://github.com/chroma-core/chroma) | 项目形态、发布与社区活动入口 |
| DB-Q1 | [Qdrant：Filtering](https://qdrant.tech/documentation/concepts/filtering/) | payload 条件、组合过滤 |
| DB-Q2 | [Qdrant Python Client](https://github.com/qdrant/qdrant-client) | 内存、本地路径、远程服务客户端形态 |
| DB-Q3 | [Qdrant：Distributed Deployment](https://qdrant.tech/documentation/scaling/distributed_deployment/) | 分布式、peer、shard/replica 部署 |
| DB-Q4 | [qdrant-client 1.19.0](https://pypi.org/project/qdrant-client/) | 本项目锁定的 Python 客户端版本 |
| DB-M1 | [Milvus：Architecture Overview](https://milvus.io/docs/architecture_overview.md) | 存算分离、水平扩展、组件架构 |
| DB-M2 | [Milvus：Main Components](https://milvus.io/docs/main_components.md) | Standalone/Cluster、etcd、对象存储、WAL |
| DB-M3 | [Milvus：Scalar Query](https://milvus.io/docs/get-and-scalar-query.md) | scalar/metadata 条件查询 |
| DB-M4 | [Milvus 官方仓库](https://github.com/milvus-io/milvus) | 项目发布与社区活动入口 |

## RAG 框架与平台

| ID | 来源 | 用途 |
|---|---|---|
| FW-LC1 | [LangChain：Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval) | Document、loader、splitter、embedding、vector store、retriever 模块化链路 |
| FW-LC2 | [LangChain 官方仓库](https://github.com/langchain-ai/langchain) | 开发框架形态与发布入口 |
| FW-LI1 | [LlamaIndex：Query Pipeline](https://docs.llamaindex.ai/en/stable/module_guides/querying/pipeline/) | 数据组件编排；Query Pipeline 已进入 feature-freeze/deprecation，官方建议 Workflows |
| FW-LI2 | [LlamaIndex 官方仓库](https://github.com/run-llama/llama_index) | 数据框架形态与发布入口 |
| FW-DI1 | [Dify：Knowledge Retrieval](https://docs.dify.ai/guides/knowledge-base/retrieval) | RAG、低代码 Workflow、Agent、API 平台能力 |
| FW-DI2 | [Dify 官方仓库](https://github.com/langgenius/dify) | 开源平台部署与发布入口 |
| FW-FG1 | [FastGPT：Quick Start](https://doc.fastgpt.io/en/guide/getting-started/quick-start) | 知识库、工作流、Agent、引用式问答 |
| FW-FG2 | [FastGPT：Workflows](https://doc.fastgpt.io/en/guide/build/workflow/intro) | 节点输入输出、触发与执行模型 |
| FW-RF1 | [RAGFlow：Quickstart](https://github.com/infiniflow/ragflow/blob/main/docs/quickstart.mdx) | 深度文档理解、可干预切块、检索测试、引用、部署前提 |
| FW-RF2 | [RAGFlow 官方仓库](https://github.com/infiniflow/ragflow) | 端到端 RAG 平台与依赖入口 |
| FW-MK1 | [MaxKB v2 产品文档](https://maxkb.cn/docs/v2/) | 知识库、RAG、Workflow、Agent 产品形态 |
| FW-MK2 | [MaxKB 高级智能体](https://maxkb.cn/docs/v2/user_manual/app/workflow_app/) | 检索、多路召回、业务节点与发布流程 |
| FW-MK3 | [MaxKB 官方仓库](https://github.com/1Panel-dev/MaxKB) | 开源平台部署与发布入口 |

## 模型、RAG 与微调

| ID | 来源 | 用途 |
|---|---|---|
| MD-E1 | [BAAI/bge-m3 模型卡](https://huggingface.co/BAAI/bge-m3) | 1024 维、8192 token、多语言、dense/sparse/multi-vector 能力 |
| MD-R1 | [BAAI/bge-reranker-v2-m3 模型卡](https://huggingface.co/BAAI/bge-reranker-v2-m3) | 多语言 query-passage 相关性评分、部署说明 |
| MD-F1 | [FlagEmbedding 1.4.0](https://pypi.org/project/FlagEmbedding/) | 本项目可选本地模型适配依赖版本 |
| MD-RAG1 | [NeurIPS 2020：Retrieval-Augmented Generation](https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html) | 参数记忆与非参数检索记忆结合的原始研究依据 |
| MD-LORA1 | [LoRA 原始论文](https://arxiv.org/abs/2106.09685) | 冻结预训练权重并训练低秩矩阵的参数高效微调方法 |
| MD-LORA2 | [Microsoft LoRA 官方实现](https://github.com/microsoft/LoRA) | LoRA 参考代码与论文入口 |

## 本项目实现依赖

| ID | 来源 | 用途 |
|---|---|---|
| IM-P1 | [pydantic-settings 2.15.0](https://pypi.org/project/pydantic-settings/) | 受校验环境配置与 SecretStr |
| IM-H1 | [HTTPX2 2.10.0](https://pypi.org/project/httpx2/) | 外部模型 HTTP、超时、MockTransport |
| IM-F1 | [FastAPI 官方文档](https://fastapi.tiangolo.com/) | API 与依赖注入 |

## 证据边界

- “本项目实测”仅指仓库内 10 个示例 Chunk、离线组件和当前测试环境，不代表生产规模性能。
- 各产品的性能没有在相同硬件、相同数据规模、相同索引参数下做横向基准，因此 D-005 不给出性能胜负数字。
- 校内 AI 平台的模型、配额、网络、数据合规与可用 API 尚未取得可验证资料；D-007 只列接入前提，不声称已经可用。
- 模型卡中的多语言、长度、维度等为官方声明；本项目默认 CI 不下载或实测大模型权重。

