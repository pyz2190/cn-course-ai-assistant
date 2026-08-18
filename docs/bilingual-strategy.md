# 中英双语知识库策略

> 状态：v1.0（2026-08-17）

## 设计目标

支持中英双语课程资料的存储、检索和引用，使系统能够：
- 接收中文和英文课程资料并生成对应 Chunk
- 根据用户提问语言自动选择合适的语料
- 在回答中提供双语引用

## 存储策略

### 方案选择：同一知识点双语 Chunk 共存

每个知识点同时维护中文和英文两个 Chunk，通过 `language` 字段区分：

```
Chunk A (language=zh): "TCP 使用三次握手同步双方的初始序列号..."
Chunk B (language=en): "TCP uses a three-way handshake to synchronize..."
```

**选择理由：**
- 保持每个 Chunk 的语义完整性
- 支持单语检索和双语对照检索
- 与现有 `ChunkMetadata` 模型兼容

### 字段规范

| 字段 | 中文 Chunk | 英文 Chunk |
|------|-----------|-----------|
| `language` | `zh` | `en` |
| `content` | 中文内容 | 英文内容 |
| `knowledge_point_ids` | 同一知识点 ID | 同一知识点 ID |
| `chapter` | 中文章节名 | 英文章节名 |
| `title` | 中文标题 | 英文标题 |

## 检索策略

### 单语提问

用户用中文提问时，优先检索 `language=zh` 的 Chunk；英文提问时优先检索 `language=en`。

### 双语对照

当用户提问涉及术语对照（如"TCP 的英文全称是什么"），同时返回中英文 Chunk。

### 关键词匹配

`KnowledgePoint` 模型的 `keywords_zh` 和 `keywords_en` 字段用于双语关键词匹配：

```json
{
  "knowledge_point_id": "kp-transport-tcp-handshake",
  "keywords_zh": ["三次握手", "TCP连接", "SYN"],
  "keywords_en": ["three-way handshake", "TCP connection", "SYN"]
}
```

## 语料来源

| 资料类型 | 中文来源 | 英文来源 |
|---------|---------|---------|
| 教材 | 《计算机网络：自顶向下方法》中文版 | Computer Networking: A Top-Down Approach |
| 实验指导 | 课程实验指导书（中文） | Course Lab Manual (English) |
| 课件 | 教师课件（中文） | Instructor Slides (English) |
| RFC | RFC 原文（英文） | RFC Original (English) |

## 实现路径

1. 为每个中文 Mock Chunk 补充对应的英文 Chunk
2. 更新 `KnowledgePoint` 的 `keywords_en` 字段
3. `MockRetriever` 根据提问语言选择 Chunk
4. `MockAnswerGenerator` 根据 Chunk 语言生成对应语言的回答

## 质量要求

- 英文 Chunk 必须是专业翻译或原版英文教材内容，不得使用机器翻译的生硬译文
- 中英文 Chunk 的知识点关联必须一致
- 术语翻译必须准确（如：拥塞控制 = Congestion Control）
