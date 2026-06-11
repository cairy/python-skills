"""render.py 页面渲染单元测试。"""

from pathlib import Path

import pytest

from pdf_tools.core import open_pdf
from pdf_tools.render import render_pages


class TestRenderPages:
    """测试 render_pages 函数。"""

    def test_render_single_page(self, sample_single_page_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "rendered"

        with open_pdf(sample_single_page_pdf) as doc:
            pages = render_pages(doc, output_dir=output_dir)

        assert len(pages) == 1
        assert pages[0].page == 1
        assert pages[0].width > 0
        assert pages[0].height > 0
        assert pages[0].path is not None
        assert Path(pages[0].path).exists()
        # 默认格式为 png
        assert pages[0].ext == "png"

    def test_render_specific_pages(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "rendered"

        with open_pdf(sample_multi_page_pdf) as doc:
            pages = render_pages(doc, pages=[1, 3], output_dir=output_dir)

        assert len(pages) == 2
        assert pages[0].page == 1
        assert pages[1].page == 3

    def test_render_all_pages(self, sample_multi_page_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "rendered"

        with open_pdf(sample_multi_page_pdf) as doc:
            pages = render_pages(doc, output_dir=output_dir)

        assert len(pages) == 5
        for i, p in enumerate(pages):
            assert p.page == i + 1
            assert Path(p.path).exists()

    def test_render_dpi(self, sample_single_page_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "rendered"

        with open_pdf(sample_single_page_pdf) as doc:
            pages_low = render_pages(doc, output_dir=output_dir, dpi=72)
            pages_high = render_pages(doc, output_dir=output_dir / "high", dpi=300)

        # 高 DPI 应该产生更大尺寸的图片
        assert pages_high[0].width > pages_low[0].width
        assert pages_high[0].height > pages_low[0].height

    def test_auto_creates_output_dir(self, sample_single_page_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "nested" / "rendered"
        assert not output_dir.exists()

        with open_pdf(sample_single_page_pdf) as doc:
            pages = render_pages(doc, output_dir=output_dir)

        assert output_dir.exists()
        assert len(pages) > 0
        assert Path(pages[0].path).exists()

    def test_render_jpeg_format(self, sample_single_page_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "rendered"

        with open_pdf(sample_single_page_pdf) as doc:
            pages = render_pages(doc, output_dir=output_dir, fmt="jpeg")

        assert pages[0].ext == "jpeg"
        assert Path(pages[0].path).exists()
