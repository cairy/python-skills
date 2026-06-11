"""core.py 单元测试。"""

from pathlib import Path

import fitz
import pytest

from pdf_tools.core import open_pdf, parse_page_ranges, parse_pdf_date


class TestOpenPdf:
    """测试 open_pdf 上下文管理器。"""

    def test_opens_valid_pdf(self, sample_single_page_pdf: Path) -> None:
        with open_pdf(sample_single_page_pdf) as doc:
            assert isinstance(doc, fitz.Document)
            assert doc.page_count == 1

    def test_document_closed_after_context(self, sample_single_page_pdf: Path) -> None:
        doc_ref: fitz.Document | None = None
        with open_pdf(sample_single_page_pdf) as doc:
            doc_ref = doc
            assert not doc.is_closed
        assert doc_ref is not None
        assert doc_ref.is_closed

    def test_raises_file_not_found(self, nonexistent_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            with open_pdf(nonexistent_path) as doc:
                pass  # pragma: no cover

    def test_raises_value_error_for_corrupted(self, corrupted_file: Path) -> None:
        with pytest.raises(ValueError):
            with open_pdf(corrupted_file) as doc:
                pass  # pragma: no cover

    def test_raises_value_error_for_encrypted_without_password(
        self, sample_encrypted_pdf: Path
    ) -> None:
        with pytest.raises(ValueError):
            with open_pdf(sample_encrypted_pdf) as doc:
                pass  # pragma: no cover

    def test_opens_encrypted_with_password(self, sample_encrypted_pdf: Path) -> None:
        with open_pdf(sample_encrypted_pdf, password="secret123") as doc:
            assert doc.page_count == 1
            assert not doc.is_closed

    def test_raises_value_error_for_wrong_password(
        self, sample_encrypted_pdf: Path
    ) -> None:
        with pytest.raises(ValueError):
            with open_pdf(sample_encrypted_pdf, password="wrong") as doc:
                pass  # pragma: no cover

    def test_raises_permission_error(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "no_read.pdf"
        doc = fitz.open()
        doc.new_page(width=612, height=792)
        doc.save(str(pdf_path))
        doc.close()
        pdf_path.chmod(0o000)
        try:
            with pytest.raises((PermissionError, OSError)):
                with open_pdf(pdf_path) as doc:
                    pass  # pragma: no cover
        finally:
            pdf_path.chmod(0o644)

    def test_raises_value_error_for_directory(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            with open_pdf(tmp_path) as doc:
                pass  # pragma: no cover


class TestParsePageRanges:
    """测试 parse_page_ranges 函数。"""

    def test_single_range(self) -> None:
        result = parse_page_ranges("1-3", max_pages=10)
        assert result == [1, 2, 3]

    def test_multiple_ranges(self) -> None:
        result = parse_page_ranges("1-3,5,7-10", max_pages=10)
        assert result == [1, 2, 3, 5, 7, 8, 9, 10]

    def test_overlapping_ranges_deduplicated(self) -> None:
        result = parse_page_ranges("1-3,2-4", max_pages=10)
        assert result == [1, 2, 3, 4]

    def test_single_page(self) -> None:
        result = parse_page_ranges("5", max_pages=10)
        assert result == [5]

    def test_reversed_range_raises(self) -> None:
        with pytest.raises(ValueError, match="倒序"):
            parse_page_ranges("5-1", max_pages=10)

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="空"):
            parse_page_ranges("", max_pages=10)

    def test_zero_page_raises(self) -> None:
        with pytest.raises(ValueError, match="页码"):
            parse_page_ranges("0-2", max_pages=10)

    def test_negative_page_raises(self) -> None:
        with pytest.raises(ValueError, match="页码"):
            parse_page_ranges("-1", max_pages=10)

    def test_out_of_bounds_raises(self) -> None:
        with pytest.raises(ValueError, match="越界"):
            parse_page_ranges("1-15", max_pages=10)

    def test_max_pages_zero_any_range_raises(self) -> None:
        with pytest.raises(ValueError, match="越界"):
            parse_page_ranges("1", max_pages=0)

    def test_strips_whitespace(self) -> None:
        result = parse_page_ranges("  1-3 , 5  ", max_pages=10)
        assert result == [1, 2, 3, 5]

    def test_single_page_equals_max(self) -> None:
        result = parse_page_ranges("10", max_pages=10)
        assert result == [10]

    def test_negative_range_start_raises(self) -> None:
        with pytest.raises(ValueError, match="页码"):
            parse_page_ranges("-1-3", max_pages=10)

    def test_negative_range_end_raises(self) -> None:
        with pytest.raises(ValueError, match="页码"):
            parse_page_ranges("3--1", max_pages=10)

    def test_empty_range_part_skipped(self) -> None:
        result = parse_page_ranges("1,,3", max_pages=10)
        assert result == [1, 3]


class TestParsePdfDate:
    """测试 parse_pdf_date 函数。"""

    def test_full_format_with_timezone(self) -> None:
        result = parse_pdf_date("D:20240115083000+08'00'")
        assert result == "2024-01-15T08:30:00+08:00"

    def test_utc_marker(self) -> None:
        result = parse_pdf_date("D:20240115083000Z")
        assert result == "2024-01-15T08:30:00Z"

    def test_no_timezone(self) -> None:
        result = parse_pdf_date("D:20240115083000")
        assert result == "2024-01-15T08:30:00"

    def test_date_only(self) -> None:
        result = parse_pdf_date("D:20240115")
        assert result == "2024-01-15"

    def test_none_returns_none(self) -> None:
        assert parse_pdf_date(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert parse_pdf_date("") is None

    def test_invalid_format_returns_none(self) -> None:
        assert parse_pdf_date("not a date") is None

    def test_negative_timezone(self) -> None:
        result = parse_pdf_date("D:20240115083000-05'00'")
        assert result == "2024-01-15T08:30:00-05:00"
