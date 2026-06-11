"""extract.py 文本提取单元测试。"""

from pathlib import Path

import fitz
import pytest

from pdf_tools.core import TextBlock, open_pdf
from pdf_tools.extract import extract_text_blocks, extract_text_plain


class TestExtractTextPlain:
    """测试 extract_text_plain 函数。"""

    def test_extracts_text(self, sample_single_page_pdf: Path) -> None:
        with open_pdf(sample_single_page_pdf) as doc:
            text = extract_text_plain(doc)

        assert "Hello PDF World" in text
        assert "Second line" in text

    def test_all_pages_by_default(self, sample_multi_page_pdf: Path) -> None:
        with open_pdf(sample_multi_page_pdf) as doc:
            text = extract_text_plain(doc)

        assert "Page 1" in text
        assert "Page 5" in text
        # 多页之间以两个换行符分隔
        assert "\n\n" in text

    def test_specific_pages(self, sample_multi_page_pdf: Path) -> None:
        with open_pdf(sample_multi_page_pdf) as doc:
            text = extract_text_plain(doc, pages=[1, 3])

        assert "Page 1" in text
        assert "Page 3" in text
        assert "Page 2" not in text
        assert "Page 5" not in text

    def test_returns_string(self, sample_single_page_pdf: Path) -> None:
        with open_pdf(sample_single_page_pdf) as doc:
            text = extract_text_plain(doc)

        assert isinstance(text, str)


class TestExtractTextBlocks:
    """测试 extract_text_blocks 函数。"""

    def test_returns_text_blocks(self, sample_single_page_pdf: Path) -> None:
        with open_pdf(sample_single_page_pdf) as doc:
            blocks = extract_text_blocks(doc)

        assert len(blocks) > 0
        assert all(isinstance(b, TextBlock) for b in blocks)
        assert blocks[0].page == 1
        assert "Hello PDF World" in blocks[0].text
        # 验证坐标是合理的正值
        assert blocks[0].x >= 0
        assert blocks[0].y >= 0
        assert blocks[0].width > 0
        assert blocks[0].height > 0

    def test_multi_page_blocks(self, sample_multi_page_pdf: Path) -> None:
        with open_pdf(sample_multi_page_pdf) as doc:
            blocks = extract_text_blocks(doc)

        # 应该有多个页面的块
        pages = {b.page for b in blocks}
        assert 1 in pages
        assert 5 in pages

    def test_specific_pages(self, sample_multi_page_pdf: Path) -> None:
        with open_pdf(sample_multi_page_pdf) as doc:
            blocks = extract_text_blocks(doc, pages=[2])

        assert all(b.page == 2 for b in blocks)
        assert any("Page 2" in b.text for b in blocks)

    def test_block_type_is_int(self, sample_single_page_pdf: Path) -> None:
        with open_pdf(sample_single_page_pdf) as doc:
            blocks = extract_text_blocks(doc)

        assert all(isinstance(b.block_type, int) for b in blocks)

    def test_empty_page_returns_empty_list(self, tmp_path: Path) -> None:
        """测试无文本层的页面返回空列表。"""
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page(width=612, height=792)  # 空页面，无文本
        doc.save(str(pdf_path))
        doc.close()

        with open_pdf(pdf_path) as doc:
            blocks = extract_text_blocks(doc)

        assert blocks == []
