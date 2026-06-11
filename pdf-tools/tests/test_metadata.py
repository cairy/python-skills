"""metadata.py 单元测试。"""

from pathlib import Path

import pytest

from pdf_tools.core import open_pdf
from pdf_tools.metadata import get_metadata


class TestGetMetadata:
    """测试 get_metadata 函数。"""

    def test_extracts_metadata(self, sample_with_metadata_pdf: Path) -> None:
        with open_pdf(sample_with_metadata_pdf) as doc:
            meta = get_metadata(doc)

        assert meta.page_count == 1
        assert meta.title == "Test Document"
        assert meta.author == "Test Author"
        assert meta.subject == "Test Subject"
        assert meta.creator == "Test Creator"
        assert meta.producer == "Test Producer"
        assert meta.creation_date == "2024-01-15T08:30:00+08:00"
        assert meta.modification_date == "2024-03-20T14:22:00Z"
        assert meta.pdf_version in ("1.4", "1.5", "1.6", "1.7")

    def test_handles_missing_metadata(self, sample_single_page_pdf: Path) -> None:
        with open_pdf(sample_single_page_pdf) as doc:
            meta = get_metadata(doc)

        assert meta.page_count == 1
        assert meta.title is None
        assert meta.author is None
        assert meta.pdf_version in ("1.4", "1.7", "1.5", "1.6")  # fitz 默认版本

    def test_multi_page_count(self, sample_multi_page_pdf: Path) -> None:
        with open_pdf(sample_multi_page_pdf) as doc:
            meta = get_metadata(doc)

        assert meta.page_count == 5
