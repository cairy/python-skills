"""pytest 共享 fixture：动态创建测试 PDF 文件。"""

import base64
from pathlib import Path
from typing import Generator

import fitz
import pytest

TEST_DIR = Path(__file__).parent


@pytest.fixture
def sample_single_page_pdf(tmp_path: Path) -> Path:
    """创建一个单页测试 PDF，包含简单文本。"""
    pdf_path = tmp_path / "sample_single.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size
    page.insert_text((72, 72), "Hello PDF World")
    page.insert_text((72, 120), "Second line of text")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_multi_page_pdf(tmp_path: Path) -> Path:
    """创建一个 5 页测试 PDF，每页有不同文本。"""
    pdf_path = tmp_path / "sample_multi.pdf"
    doc = fitz.open()
    for i in range(1, 6):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Page {i} content")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_encrypted_pdf(tmp_path: Path) -> Path:
    """创建一个带密码的测试 PDF。"""
    pdf_path = tmp_path / "sample_encrypted.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Secret content")
    # 使用用户密码加密
    doc.save(str(pdf_path), encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner123", user_pw="secret123")
    doc.close()
    return pdf_path


@pytest.fixture
def sample_with_image_pdf(tmp_path: Path) -> Path:
    """创建一个包含嵌入图片的测试 PDF。"""
    pdf_path = tmp_path / "sample_with_image.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Document with image")

    # 创建一个简单的 100x50 RGB 图片数据 (red rectangle)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 50))
    for y in range(50):
        for x in range(100):
            pix.set_pixel(x, y, (255, 0, 0))

    # 将 Pixmap 作为图像插入页面
    img_rect = fitz.Rect(72, 150, 172, 200)
    page.insert_image(img_rect, pixmap=pix)
    pix = None  # release

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def sample_with_metadata_pdf(tmp_path: Path) -> Path:
    """创建一个带完整元数据的测试 PDF。"""
    pdf_path = tmp_path / "sample_metadata.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Document with metadata")

    doc.set_metadata({
        "title": "Test Document",
        "author": "Test Author",
        "subject": "Test Subject",
        "creator": "Test Creator",
        "producer": "Test Producer",
        "creationDate": "D:20240115083000+08'00'",
        "modDate": "D:20240320142200Z",
    })
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def nonexistent_path() -> Path:
    """返回一个确定不存在的文件路径。"""
    return Path("/tmp/nonexistent_file_12345.pdf")


@pytest.fixture
def corrupted_file(tmp_path: Path) -> Path:
    """创建一个损坏的"PDF"文件（不是有效的 PDF）。"""
    path = tmp_path / "corrupted.pdf"
    path.write_bytes(b"This is not a valid PDF file content")
    return path
