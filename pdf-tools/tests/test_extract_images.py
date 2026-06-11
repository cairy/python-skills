"""extract.py 图片提取单元测试。"""

import base64
from pathlib import Path

import pytest

from pdf_tools.core import open_pdf
from pdf_tools.extract import extract_images


class TestExtractImages:
    """测试 extract_images 函数。"""

    def test_extract_images_files_mode(self, sample_with_image_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        with open_pdf(sample_with_image_pdf) as doc:
            images = extract_images(
                doc,
                output_mode="files",
                output_dir=output_dir,
            )

        assert len(images) > 0
        assert images[0].page == 1
        assert images[0].width > 0
        assert images[0].height > 0
        assert images[0].path is not None
        assert images[0].base64_data is None
        # 文件实际存在
        assert Path(images[0].path).exists()

    def test_extract_images_base64_mode(self, sample_with_image_pdf: Path) -> None:
        with open_pdf(sample_with_image_pdf) as doc:
            images = extract_images(doc, output_mode="base64")

        assert len(images) > 0
        assert images[0].base64_data is not None
        assert images[0].path is None
        # base64 应该可解码
        data = base64.b64decode(images[0].base64_data)
        assert len(data) > 0

    def test_specific_pages(self, sample_with_image_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        with open_pdf(sample_with_image_pdf) as doc:
            images = extract_images(
                doc,
                pages=[1],
                output_mode="files",
                output_dir=output_dir,
            )

        assert all(img.page == 1 for img in images)

    def test_files_mode_requires_output_dir(self, sample_with_image_pdf: Path) -> None:
        with open_pdf(sample_with_image_pdf) as doc:
            with pytest.raises(ValueError, match="output_dir"):
                extract_images(doc, output_mode="files")

    def test_ext_is_valid_format(self, sample_with_image_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "images"
        output_dir.mkdir()

        with open_pdf(sample_with_image_pdf) as doc:
            images = extract_images(
                doc,
                output_mode="files",
                output_dir=output_dir,
            )

        assert len(images) > 0
        # ext 应该是有效的图片格式
        assert images[0].ext in ("png", "jpeg", "jpg")

    def test_auto_creates_output_dir(self, sample_with_image_pdf: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "nested" / "images"
        # 目录不存在
        assert not output_dir.exists()

        with open_pdf(sample_with_image_pdf) as doc:
            images = extract_images(
                doc,
                output_mode="files",
                output_dir=output_dir,
            )

        assert output_dir.exists()
        assert len(images) > 0
        assert Path(images[0].path).exists()
