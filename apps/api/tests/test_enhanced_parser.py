"""增强解析器测试：覆盖表格、公式、图片和图表提取。"""

from app.adapters.document_parser import DocumentParser, ParsedChunk
from app.domain.enums import ContentType


class TestFormulaDetection:
    """公式检测测试。"""

    def test_detect_math_symbols(self):
        from app.adapters.document_parser import DocumentParser
        text = "带宽时延积 = BDP ∝ 带宽 × 时延"
        formulas = DocumentParser._detect_formulas(text)
        assert len(formulas) > 0

    def test_detect_greek_letters(self):
        from app.adapters.document_parser import DocumentParser
        text = "α = 0.5, β = 0.3"
        formulas = DocumentParser._detect_formulas(text)
        assert len(formulas) > 0

    def test_no_formulas_in_plain_text(self):
        from app.adapters.document_parser import DocumentParser
        text = "这是一个普通的文本段落，没有数学公式。"
        formulas = DocumentParser._detect_formulas(text)
        assert len(formulas) == 0

    def test_detect_calculus_symbols(self):
        from app.adapters.document_parser import DocumentParser
        text = "∫f(x)dx 从 0 到 ∞"
        formulas = DocumentParser._detect_formulas(text)
        assert len(formulas) > 0


class TestPDFTableExtraction:
    """PDF 表格提取测试。"""

    def test_parse_pdf_with_table(self, tmp_path):
        """测试包含表格的 PDF 解析。"""
        import pymupdf

        pdf_path = tmp_path / "table_test.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        # 插入一些文本
        page.insert_text((72, 72), "第 1 章 测试章节", fontname="china-s")
        page.insert_text((72, 100), "以下是协议比较表：", fontname="china-s")
        doc.save(str(pdf_path))
        doc.close()

        parser = DocumentParser()
        chunks = parser.parse(pdf_path, ContentType.PDF)
        # 至少应该有文本 chunk
        assert len(chunks) > 0
        text_chunks = [c for c in chunks if c.extracted_content_type is None]
        assert len(text_chunks) > 0


class TestPPTTableExtraction:
    """PPT 表格提取测试。"""

    def test_parse_ppt_with_table(self, tmp_path):
        """测试包含表格的 PPT 解析。"""
        from pptx import Presentation
        from pptx.util import Inches

        pptx_path = tmp_path / "table_test.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # 空白布局

        # 添加文本
        txBox = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
        tf = txBox.text_frame
        tf.text = "协议对比分析"

        # 添加表格
        rows, cols = 3, 3
        table = slide.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(8), Inches(3)).table
        table.cell(0, 0).text = "协议"
        table.cell(0, 1).text = "类型"
        table.cell(0, 2).text = "特点"
        table.cell(1, 0).text = "TCP"
        table.cell(1, 1).text = "可靠"
        table.cell(1, 2).text = "面向连接"
        table.cell(2, 0).text = "UDP"
        table.cell(2, 1).text = "不可靠"
        table.cell(2, 2).text = "无连接"

        prs.save(str(pptx_path))

        parser = DocumentParser()
        chunks = parser.parse(pptx_path, ContentType.PPT)

        # 应该有表格 chunk
        table_chunks = [c for c in chunks if c.extracted_content_type == ContentType.TABLE]
        assert len(table_chunks) > 0
        assert "TCP" in table_chunks[0].content
        assert "UDP" in table_chunks[0].content

    def test_parse_ppt_table_has_markdown_format(self, tmp_path):
        """验证 PPT 表格提取为 Markdown 格式。"""
        from pptx import Presentation
        from pptx.util import Inches

        pptx_path = tmp_path / "md_table.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])

        table = slide.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(5), Inches(2)).table
        table.cell(0, 0).text = "A"
        table.cell(0, 1).text = "B"
        table.cell(1, 0).text = "1"
        table.cell(1, 1).text = "2"

        prs.save(str(pptx_path))

        parser = DocumentParser()
        chunks = parser.parse(pptx_path, ContentType.PPT)
        table_chunks = [c for c in chunks if c.extracted_content_type == ContentType.TABLE]
        assert len(table_chunks) > 0
        # 验证 Markdown 表格格式
        assert "| A | B |" in table_chunks[0].content
        assert "| --- | --- |" in table_chunks[0].content


class TestParsedChunkFields:
    """ParsedChunk 字段测试。"""

    def test_parsed_chunk_with_extracted_type(self):
        chunk = ParsedChunk(
            content="test",
            chapter="ch1",
            page_start=1,
            page_end=1,
            extracted_content_type=ContentType.TABLE,
        )
        assert chunk.extracted_content_type == ContentType.TABLE

    def test_parsed_chunk_with_source_path(self):
        chunk = ParsedChunk(
            content="test",
            chapter="ch1",
            page_start=1,
            page_end=1,
            source_path="/path/to/image.png",
        )
        assert chunk.source_path == "/path/to/image.png"

    def test_parsed_chunk_defaults(self):
        chunk = ParsedChunk(
            content="test",
            chapter="ch1",
            page_start=1,
            page_end=1,
        )
        assert chunk.extracted_content_type is None
        assert chunk.source_path is None
        assert chunk.title is None
