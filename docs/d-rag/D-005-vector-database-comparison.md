# D-005｜向量数据库对比表

> 版本：v1.0
> 调研日期：2026-08-16
> 对比对象：Chroma、Qdrant、Milvus
> 结论：本项目选择 Qdrant；通过 `VectorStore` 端口保留替换能力。

## 1. 结论先行

本项目当前只有 10 个课程 Chunk，但需要真实向量检索、课程/知识点/资源/访问级别过滤、Windows/macOS/Linux 的本地开发，以及未来切到远程服务的路径。Qdrant Python Client 可用同一调用模型覆盖内存、本地目录和远程服务，payload filter 能直接承载 B 的 metadata，因而在“开发便利性—过滤能力—后续扩展”之间最平衡。[DB-Q1][DB-Q2]

Chroma 更适合最快速的嵌入式原型；Milvus 的分布式架构更适合大规模、高负载场景，但对当前三周课程项目属于明显过度部署。[DB-C1][DB-C2][DB-M1][DB-M2]

## 2. 统一维度对比

| 维度 | Chroma | Qdrant | Milvus |
|---|---|---|---|
| 产品定位 | 面向 AI 应用的 embedding/document collection | 专用向量数据库，payload 与向量共同检索 | 面向大规模向量检索的云原生数据库 |
| 部署复杂度 | 低；本地 client 或 client-server 起步快 | 低到中；Python 本地模式、单服务、分布式均有路径 | 中到高；Standalone 可起步，Cluster 涉及多个组件与外部存储 |
| 检索能力 | 相似度检索；可直接传 query embedding | 相似度检索、payload filter、可扩展到分布式 shard/replica | 多类 ANN 索引、scalar/vector 组合查询、分布式查询 |
| 元数据过滤 | `where` 与 `where_document` | typed payload condition、must/should/must_not、嵌套组合 | scalar field expression 与向量查询组合 |
| 持久化 | Persistent Client 或 server | 本地目录、服务端存储；本项目测试用 `:memory:` | Standalone 本地组件；Cluster 使用 meta/object/WAL 等存储组件 |
| 扩展性 | 适合小中型原型；更大规模需评估服务形态 | 单机到分布式路径连续，支持 peer 和分片/副本 | 存算分离、计算节点水平扩展，面向大规模和高负载 |
| 社区活跃度 | 官方仓库持续发布；本报告不以 star 数代替质量 | 官方仓库与文档持续发布；Python Client 独立维护 | Linux Foundation 生态项目，官方仓库与版本文档持续维护 |
| 当前项目适用性 | 可用，但从嵌入式到远程服务的工程形态与本项目目标不如 Qdrant 统一 | **最适合**：过滤字段、三种运行形态和 Python 接口与需求直接匹配 | 能力充足但运维面过重，10 个 Chunk 无法体现其规模优势 |
| 主要风险 | 服务化、运维与高级过滤能力需按目标版本复核 | 本地模式不是生产高可用方案；远程部署仍需备份、认证和容量治理 | 组件多、学习与运维成本高；Standalone 到 Cluster 的升级需单独规划 |
| 证据 | [DB-C1][DB-C2][DB-C3] | [DB-Q1][DB-Q2][DB-Q3][DB-Q4] | [DB-M1][DB-M2][DB-M3][DB-M4] |

## 3. 检索性能说明

三者未在相同硬件、数据规模、索引算法、召回率目标与并发下做公平基准，因此本报告不引用不可比的 QPS/延迟数字，也不声称 Qdrant 性能领先。

本项目实测仅验证“选定方案满足当前原型”：Qdrant 内存模式导入 10 个 Chunk 后，20 次预热后离线问答样本最大耗时约 2.604 ms（Windows、Python 3.11；包含查询编码、检索、重排和离线抽取，不包含外部模型生成）。该结果只说明远低于本项目 2 秒门槛，不可外推到生产数据量。

## 4. 本项目落地映射

| 需求 | Qdrant 落地 |
|---|---|
| 幂等写入 | `course_id + chunk_id` 生成确定性 UUID |
| 课程隔离 | payload `course_id` 的 must filter |
| 知识点范围 | payload `knowledge_point_ids` 的 MatchAny |
| 资料范围 | payload `resource_id` 的 MatchAny |
| 权限边界 | 服务端生成 `allowed_access_levels` filter，客户端不能扩大 |
| 元数据保真 | payload 保存完整 `ChunkMetadata`，Citation 从服务端回填 |
| 测试 | `QdrantClient(location=":memory:")`，不访问网络 |
| 本地持久化 | `QdrantClient(path=...)` |
| 后续服务化 | `QdrantClient(url=..., api_key=...)`，SecretStr 注入 |

## 5. 选型与替换条件

正式基线为 `qdrant-client==1.19.0`。若后续出现以下情况，重新评审：

- 仅需单机、极简文档原型且不再计划服务化，可重新比较 Chroma 的总体维护成本。
- 数据达到大规模分布式检索、复杂混合检索或团队已具备 Milvus 运维平台，可用同一验收集比较 Milvus。
- 任何替换必须通过 `VectorStore` 契约、元数据往返测试、过滤越界测试和 C 的评测集，不允许调用方直接依赖厂商 SDK。

## 参考来源

来源 ID 与链接见 [research-sources.md](research-sources.md)。
