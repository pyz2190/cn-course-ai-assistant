# D-004｜AI + 向量数据库 + RAG 技术方案

> 版本：v1.0
> 定稿日期：2026-08-16
> 代码分支：`feat/d-rag-backend`
> 技术基线：原生轻量编排、Qdrant、默认离线、可选 BGE 与 OpenAI-compatible 生成

## 1. 目标与边界

本方案把 B 提供的 10 个结构化课程 Chunk 接入真实向量索引与检索，完成范围过滤、可选重排、基于证据回答、按句引用、异常降级和 C 的评测入口，同时保持现有 FastAPI/Web 请求兼容。

不包含 Canvas/LTI/身份/成绩回写，不承担 B 的 PDF/PPT/字幕解析，不修改 C 的标准答案，不实现 E 的任务引擎，不执行 LoRA 训练。

## 1.5 RAG 为什么适合课程问答

在把课程资料接入模型之前，需要先回答"为什么用 RAG 而不是别的做法"。
课程问答有四个特征，正好对应 RAG 的四项能力。

### 1.5.1 答案必须可核对到课程资料

学生问"三次握手为什么是三次"，只给一段正确的解释是不够的——
他还需要知道这个结论出自教材哪一章、哪一页，以便回去精读和复习。
一个不能被核对的答案在教学场景中价值有限，出错时更无法追责和修正。

RAG 天然满足这一点：回答由检索到的 Chunk 生成，每个 Chunk 都带
`resource_id`、`chapter` 和页码，因此**引用不是事后附加的装饰，
而是生成过程的输入**。纯参数化的模型无法给出这种可核对的出处。

### 1.5.2 错误答案的代价高于"没有答案"

助教答错一道题，学生会把错误结论带进考试和实验。
在教学场景中，"课程资料中没有足够证据"是一个**可接受的回答**，
而一段听起来合理但无出处的编造不是。

RAG 使这种拒答变得可实现：检索不到足够证据时直接拒答，
而不是让模型自由发挥。本方案第 6 节的引用安全设计
把这条原则落成了硬约束——模型即使虚构资源名也无法进入最终引用。
D-003 第 7.3 节实测的 30 题中有 8 题走的正是这条安全路径。

### 1.5.3 课程资料会变，模型不该跟着变

教材会换版次，实验指导每学期都在改，RFC 会被新 RFC 废止。
如果把课程知识固化进模型权重，每次资料更新都要重新训练一轮。

RAG 把知识放在可替换的外部语料里：更新资料只需重新解析、切块、入库，
**模型完全不动**。本项目的 `POST /api/v1/resources/upload` 上传后
新资料立即可被检索和引用，正是这一特性的体现。
微调与 RAG 的适用边界见 [D-007](D-007-finetuning-deployment-analysis.md) 第 2 节。

### 1.5.4 课程语料规模小，但要求精确

一门课的核心资料是教材若干章加实验指导，规模远小于通用语料，
却要求在术语、协议字段和数值上完全精确。这种"小而精"的场景
不足以支撑微调（样本量不够，且容易过拟合到少量表述），
但对检索非常友好——语料越聚焦，检索的信噪比越高。

### 1.5.5 小结

| 课程问答的要求 | RAG 的对应能力 | 本项目的实现 |
|---|---|---|
| 答案可核对到章节页码 | 检索片段携带完整元数据 | `Citation` 由服务端从 `ChunkMetadata` 回填 |
| 宁可拒答也不能编造 | 无证据即不生成 | 第 6 节的引用安全与安全拒答 |
| 资料更新不重训模型 | 知识在语料而非权重中 | `/resources/upload` 后即时生效 |
| 小规模语料下的精确回答 | 聚焦语料提高检索信噪比 | 课程范围与知识点过滤 |

RAG 结合参数记忆与非参数检索记忆的原始依据见 [MD-RAG1]。

## 2. 技术选型

| 层 | 当前默认 | 可选正式组件 | 选择依据 |
|---|---|---|---|
| 编排 | 原生 `RagService` | 后续可评估 LangChain/LlamaIndex | 链路短、边界显式、易做无网络测试 |
| 向量库 | Qdrant memory | Qdrant local/remote | 三种运行形态、payload 过滤、Python Client 统一 |
| Embedding | `offline-hash-v1-384d` | `BAAI/bge-m3` | 默认确定性无下载；正式模型支持多语言 |
| Reranker | `offline-overlap-v1` | `BAAI/bge-reranker-v2-m3` | 默认可解释；正式模型直接做 query-passage 评分 |
| Generator | `offline-extractive-v1` | OpenAI-compatible Chat Completions | 无密钥可运行；厂商中立 HTTP 边界 |
| 配置 | Pydantic Settings | 同一机制 | 环境变量校验、SecretStr、范围约束 |
| HTTP | HTTPX2 2.10.0 | 同一机制 | 独立 connect/read/write/pool timeout、MockTransport |

向量库详细对比见 D-005，框架/平台对比见 D-006，模型与部署见 D-007。模型与 RAG 原理来源见 [MD-E1][MD-R1][MD-RAG1]。

## 3. 总体架构

```text
Web / API AskRequest                 C Evaluation Runner
          │                                  │
          └───────────┬──────────────────────┘
                      ▼
                 QaService / InProcessRagAdapter
                      ▼
                   RagService
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
   IndexManager  RetrievalPipeline  Generation + CitationAssembler
        │             │              │
        ▼             ▼              ▼
 B ChunkMetadata  Embedding → Qdrant → Reranker → GroundedGenerator
```

领域层不导入 FastAPI、Qdrant、HTTPX2 或评测脚本。四个可替换端口为 `EmbeddingProvider`、`VectorStore`、`Reranker`、`GroundedGenerator`；调用方只依赖 `RagService`。

## 4. 索引流程

1. B 的 `MOCK_CHUNKS` 提供 chunk_id、resource_id、知识点、标题、正文、章节、页码、语言、内容类型、版本、访问级别和更新时间。
2. `corpus_fingerprint` 对按 chunk_id 排序后的完整 metadata 与 Embedding ID 做 SHA-256；Chunk 顺序变化不改变指纹，内容/版本变化会改变。
3. `IndexManager` 确认向量维度和 collection；同一服务内语料指纹未变且点数一致时复用索引。
4. Embedding 文本由标题、章节、知识点和正文组成。
5. Qdrant 点 ID 由 `course_id + chunk_id` 生成 UUID5，重复 upsert 不增加点数。
6. payload 保存 course_id、resource_id、knowledge_point_ids、access_level 与完整 ChunkMetadata。

本项目实测：连续两次写入 B 的 10 个 Chunk 后点数仍为 10，第二次相同索引不再次调用文档 Embedding。

## 5. 检索与过滤

请求可选携带：

```json
{
  "course_id": "computer-networks",
  "user_id": "student-demo",
  "question": "TCP 为什么需要三次握手？",
  "knowledge_point_ids": ["kp-transport-tcp-handshake"],
  "resource_ids": ["resource-000"],
  "task_id": "task-protocol-tcp-handshake"
}
```

`QaService` 不向 RAG 传 user ID；它只构造 `RetrievalScope`。course、knowledge point、resource 和服务端允许的 access level 被转换为 Qdrant filter，在检索阶段生效。task_id 保留给 E 对齐，但 D 不实现任务逻辑。

默认 `fetch_k=8`、`top_k=3`、最低分数 0.15。开启重排时先取候选、再按最终相关性阈值筛选；关闭或重排失败时使用原始向量分数，并明确记录 `disabled-or-degraded`。

测试覆盖 TCP、DNS、HTTP、路由、Wireshark 五类问题，以及知识点、资源和课程范围不越界。

## 6. 生成与引用安全

生成器输出结构是 `GroundedSentence(text, evidence_ids)`，没有 resource、title、chapter、page 等字段。`CitationAssembler` 只接受本次 `RetrievedChunk` 中存在的 evidence ID：

1. 为首次出现的合法 evidence ID 分配稳定角标 `[1]`、`[2]`。
2. 将角标挂到对应事实句末尾。
3. 从服务器端 ChunkMetadata 回填 Citation。
4. 丢弃不存在的 evidence ID；如果没有任何合法事实句/引用，转为“课程资料中没有足够证据”的安全拒答。

因此外部模型即使输出虚构资源名或不存在的 ID，也不能进入最终 Citation。引用 quote、页码和章节都来自 B 的实际 Chunk。

## 7. 两种运行模式

### 7.1 Offline（默认）

- 确定性 384 维 char/word-fragment feature hashing Embedding。
- 确定性词项重叠 Reranker，并对实验意图（Wireshark/抓包/实验等）做教学语境门控。
- 抽取最高证据 Chunk 的原句生成回答。
- Qdrant memory 测试；可改 local path 持久化。
- 不需要密钥、网络或模型下载。

这些离线组件是开发/测试基线，不宣称具有 BGE/LLM 的正式质量。

### 7.2 External（可选）

- Embedding/Reranker 可切到 FlagEmbedding 懒加载的 BGE 模型。
- Generator 使用 OpenAI-compatible `/chat/completions`，temperature=0，要求严格 JSON sentences/evidence_ids。
- API Key 使用 SecretStr 和环境变量，只放 Authorization header；请求正文不含 user ID、C 的 expected answer 或 annotation key points。
- 外部调用失败时，若允许降级则回退离线抽取并标记 `degraded=true`。

调用方不因模式切换而修改。

## 8. C 评测对接

调用方式为同进程 Python：`app.adapters.evaluation.InProcessRagAdapter`。

```text
RagRequest(evaluation_id, question, knowledge_point_ids)
    → RetrievalScope + RagExecutionOptions
    → RagService.answer
    → generated_answer + citations + asdict(RagRuntime)
```

适配器的类型表面没有 expected_answer/key_points；测试还使用“看似泄露”的对象验证这些字段不会进入 RagService。运行元数据包括实际 model、embedding、reranker、top_k/fetch_k、三阶段耗时、vector store 和 corpus version。单条异常由 C 的 runner 记录后继续。

命令：

```bash
python scripts/evaluate.py --adapter rag --dry-run
```

截至定稿日，C 的正式 evaluation_set 为空，因此 dry-run 按约定返回成功 no-op；不伪造正式评测结论。

## 9. 降级矩阵

| 故障 | 行为 | 是否编造内容 |
|---|---|---:|
| 无检索结果 | 安全拒答，Citation 为空 | 否 |
| 最终相关性低于阈值 | 安全拒答 | 否 |
| Reranker 禁用 | 返回符合阈值的初检结果，标记未重排 | 否 |
| Reranker 超时/异常 | `allow_degraded=true` 时回退初检 | 否 |
| 外部模型未配置 | 配置校验失败；默认仍用 Offline | 否 |
| 外部模型连接/读取超时 | 最多重试 1 次，再回退 Offline | 否 |
| 外部模型 5xx | 有限重试，再回退 Offline | 否 |
| 响应 JSON 非法或 evidence ID 无效 | 不输出无引用事实；必要时安全拒答 | 否 |
| 单条评测失败 | C runner 记录 error，继续后续条目 | 否 |

## 10. 配置基线

| 配置 | 默认值 |
|---|---|
| mode | `offline` |
| vector_store | `memory` |
| offline_embedding_dimension | 384 |
| top_k / fetch_k | 3 / 8 |
| max_top_k | 10（服务端校验） |
| min_retrieval_score | 0.15 |
| reranker_enabled | true |
| allow_degraded | true |
| connect/read/write/pool timeout | 3 / 30 / 10 / 3 秒 |
| max_retries | 1 |

远程 URL、API Key、模型 ID、Qdrant 路径等均通过 `CN_AI_*` 环境变量注入。

## 11. 验证结果

### 自动测试

- 完整 API/评测回归：109 项通过（2026-08-16，本地 Python 3.11）。
- Ruff：`apps/api` 与 `scripts` 全通过。
- OpenAPI/TypeScript 契约检查通过。
- 默认测试使用 Qdrant memory、MockTransport 和 Fake loader，不下载大型模型、不访问外部模型、不产生付费调用。

### 性能实测

命令：`python apps/api/scripts/benchmark_rag.py`。

在当前 Windows/Python 3.11 环境、B 的 10 个示例 Chunk、5 个问题、预热后 20 次样本中：p50 约 1.178 ms、p95 约 2.603 ms、最大约 2.604 ms。测量包含离线查询编码、Qdrant 内存检索、离线重排、离线生成与引用组装，不包含外部模型生成。

该结果仅用于验证本项目 2 秒门槛，不代表大规模语料或并发性能。

## 12. 已知限制与后续

- B 当前 Chunk 是项目示例语料；C 尚无已审批的正式引用评测集。
- Offline Hash Embedding 不是语义模型，正式质量需要 BGE 与 C 评测验证。
- Qdrant memory 不提供生产持久化/高可用；正式部署应选择 local/remote 并补备份、认证与监控。
- 外部生成链路已通过 MockTransport 验证，但没有执行付费真实模型调用。
- 校内 AI 平台和 Canvas 能力未知，不能写为已接入。

## 参考来源

来源 ID 与链接见 [research-sources.md](research-sources.md)。
