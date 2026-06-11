"""core.py 单元测试。"""

from pathlib import Path

import fitz
import pytest

from pdf_tools.core import open_pdf


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
