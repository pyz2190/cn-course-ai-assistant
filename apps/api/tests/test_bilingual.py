"""中英双语知识库测试。"""

from app.adapters.mock import MOCK_CHUNKS, MOCK_CHUNKS_EN, MOCK_CHUNKS_ZH, MockRetriever
from app.domain.enums import Language


class TestBilingualData:
    """双语语料测试。"""

    def test_zh_chunks_exist(self):
        assert len(MOCK_CHUNKS_ZH) > 0
        assert all(c.language == Language.ZH for c in MOCK_CHUNKS_ZH)

    def test_en_chunks_exist(self):
        assert len(MOCK_CHUNKS_EN) > 0
        assert all(c.language == Language.EN for c in MOCK_CHUNKS_EN)

    def test_zh_en_same_knowledge_points(self):
        """中英文 Chunk 覆盖相同的知识点集合。"""
        zh_kps = {kp for c in MOCK_CHUNKS_ZH for kp in c.knowledge_point_ids}
        en_kps = {kp for c in MOCK_CHUNKS_EN for kp in c.knowledge_point_ids}
        assert zh_kps == en_kps

    def test_combined_chunks(self):
        assert len(MOCK_CHUNKS) == len(MOCK_CHUNKS_ZH) + len(MOCK_CHUNKS_EN)


class TestBilingualRetrieval:
    """双语检索测试。"""

    def test_chinese_question_returns_zh_chunk(self):
        retriever = MockRetriever()
        chunks = retriever.retrieve("TCP 为什么需要三次握手？", "course-cn")
        assert len(chunks) > 0
        assert chunks[0].language == Language.ZH

    def test_english_question_returns_en_chunk(self):
        retriever = MockRetriever()
        chunks = retriever.retrieve("Why does TCP need a three-way handshake?", "course-cn")
        assert len(chunks) > 0
        assert chunks[0].language == Language.EN

    def test_dns_chinese(self):
        retriever = MockRetriever()
        chunks = retriever.retrieve("DNS 解析过程是什么？", "course-cn")
        assert chunks[0].language == Language.ZH

    def test_dns_english(self):
        retriever = MockRetriever()
        chunks = retriever.retrieve("How does DNS resolution work?", "course-cn")
        assert chunks[0].language == Language.EN

    def test_is_english_detection(self):
        assert MockRetriever._is_english_question("What is TCP?") is True
        assert MockRetriever._is_english_question("TCP 是什么协议？") is False
        assert MockRetriever._is_english_question("DNS 的解析过程是怎样的？") is False
        assert MockRetriever._is_english_question("How does HTTP work?") is True

    def test_fallback_language(self):
        """无法匹配关键词时，返回对应语言的第一个 chunk。"""
        retriever = MockRetriever()
        zh_chunks = retriever.retrieve("未知问题", "course-cn")
        assert zh_chunks[0].language == Language.ZH

        en_chunks = retriever.retrieve("unknown question", "course-cn")
        assert en_chunks[0].language == Language.EN
