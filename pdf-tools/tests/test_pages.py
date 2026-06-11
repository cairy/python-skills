"""pages.py 单元测试。"""

from pathlib import Path

import fitz
import pytest

from pdf_tools.core import open_pdf
from pdf_tools.pages import merge_pdfs, rotate_pages, split_pages


class TestSplitPages:
    """测试 split_pages 函数。"""

    def test_extract_single_page(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "split_out.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            result = split_pages(doc, pages=[1], output_path=output)

        assert result == str(output)
        assert output.exists()

        with open_pdf(output) as doc2:
            assert doc2.page_count == 1
            text = doc2[0].get_text()
            assert "Page 1" in text

    def test_extract_multiple_pages(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "split_out.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            result = split_pages(doc, pages=[1, 3, 5], output_path=output)

        assert result == str(output)
        with open_pdf(output) as doc2:
            assert doc2.page_count == 3
            assert "Page 1" in doc2[0].get_text()
            assert "Page 3" in doc2[1].get_text()
            assert "Page 5" in doc2[2].get_text()

    def test_empty_pages_raises(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "split_out.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            with pytest.raises(ValueError, match="空"):
                split_pages(doc, pages=[], output_path=output)

    def test_out_of_bounds_pages_raises(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "split_out.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            with pytest.raises(ValueError, match="越界"):
                split_pages(doc, pages=[1, 10], output_path=output)


class TestMergePdfs:
    """测试 merge_pdfs 函数。"""

    def test_merge_two_pdfs(self, sample_single_page_pdf: Path, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "merged.pdf"
        result = merge_pdfs(
            input_paths=[sample_single_page_pdf, sample_multi_page_pdf],
            output_path=output,
        )

        assert result == str(output)
        assert output.exists()

        with open_pdf(output) as doc:
            assert doc.page_count == 6  # 1 + 5

    def test_empty_input_raises(self, tmp_path: Path) -> None:
        output = tmp_path / "merged.pdf"
        with pytest.raises(ValueError, match="空"):
            merge_pdfs(input_paths=[], output_path=output)

    def test_merge_preserves_page_sizes(self, sample_single_page_pdf: Path, tmp_path: Path) -> None:
        # 创建不同尺寸的 PDF
        small_pdf = tmp_path / "small.pdf"
        doc_small = fitz.open()
        doc_small.new_page(width=400, height=300)
        doc_small.save(str(small_pdf))
        doc_small.close()

        output = tmp_path / "merged.pdf"
        merge_pdfs(
            input_paths=[sample_single_page_pdf, small_pdf],
            output_path=output,
        )

        with open_pdf(output) as doc:
            assert doc.page_count == 2
            # 第一页尺寸（来自 sample_single_page_pdf）
            rect1 = doc[0].rect
            assert rect1.width == 612
            assert rect1.height == 792
            # 第二页尺寸（来自 small_pdf）
            rect2 = doc[1].rect
            assert rect2.width == 400
            assert rect2.height == 300


class TestRotatePages:
    """测试 rotate_pages 函数。"""

    def test_rotate_specific_pages(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "rotated.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            result = rotate_pages(doc, output_path=output, pages=[1, 3], angle=90)

        assert result == str(output)

        with open_pdf(output) as doc2:
            # 检查旋转后的页面矩形（宽高互换）
            # 原始 Letter 尺寸: 612 x 792
            # 旋转 90 度后: 792 x 612
            page1 = doc2[0]
            assert abs(page1.rect.width - 792) < 1
            assert abs(page1.rect.height - 612) < 1

            # page3 也在旋转列表中
            page3 = doc2[2]
            assert abs(page3.rect.width - 792) < 1
            assert abs(page3.rect.height - 612) < 1

            # 未旋转的页面保持原尺寸
            page2 = doc2[1]
            assert abs(page2.rect.width - 612) < 1
            assert abs(page2.rect.height - 792) < 1

            page4 = doc2[3]
            assert abs(page4.rect.width - 612) < 1
            assert abs(page4.rect.height - 792) < 1

            page5 = doc2[4]
            assert abs(page5.rect.width - 612) < 1
            assert abs(page5.rect.height - 792) < 1

    def test_invalid_angle_raises(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "rotated.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            with pytest.raises(ValueError, match="旋转角度"):
                rotate_pages(doc, output_path=output, pages=[1], angle=45)

    def test_all_valid_angles(self, sample_single_page_pdf: Path, tmp_path: Path) -> None:
        for angle in [0, 90, 180, 270]:
            output = tmp_path / f"rotated_{angle}.pdf"
            with open_pdf(sample_single_page_pdf) as doc:
                result = rotate_pages(doc, output_path=output, pages=[1], angle=angle)
            assert result == str(output)
            assert output.exists()

    def test_out_of_bounds_pages_raises(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output = tmp_path / "rotated.pdf"
        with open_pdf(sample_multi_page_pdf) as doc:
            with pytest.raises(ValueError, match="越界"):
                rotate_pages(doc, output_path=output, pages=[10], angle=90)

