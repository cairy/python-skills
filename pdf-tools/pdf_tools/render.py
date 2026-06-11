"""PDF 页面渲染为图片。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Union

import fitz


@dataclass
class RenderedPage:
    """渲染后的页面图片信息。"""

    page: int
    width: int
    height: int
    ext: str
    path: str


def render_pages(
    doc: fitz.Document,
    pages: Optional[List[int]] = None,
    output_dir: Union[str, Path] = ".",
    dpi: int = 200,
    fmt: Literal["png", "jpeg"] = "png",
) -> List[RenderedPage]:
    """将 PDF 页面渲染为图片文件。

    使用 PyMuPDF 的 get_pixmap 进行页面光栅化，输出包含页面上所有
    可见内容（文本、嵌入图片、矢量图形等）的完整渲染图。

    Args:
        doc: PDF Document
        pages: 要渲染的页码列表（1-based），None 表示全部页面
        output_dir: 输出目录
        dpi: 渲染分辨率（每英寸像素数）
        fmt: 输出图片格式

    Returns:
        List[RenderedPage]: 渲染后的页面信息列表
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    page_indices = pages if pages is not None else list(range(1, doc.page_count + 1))
    rendered: List[RenderedPage] = []

    zoom = dpi / 72.0  # PDF 默认 72 DPI
    mat = fitz.Matrix(zoom, zoom)

    for p in page_indices:
        page = doc[p - 1]
        pix = page.get_pixmap(matrix=mat)

        filename = f"page_{p:04d}.{fmt}"
        file_path = output_path / filename
        pix.save(str(file_path))

        rendered.append(
            RenderedPage(
                page=p,
                width=pix.width,
                height=pix.height,
                ext=fmt,
                path=str(file_path),
            )
        )

    return rendered
