"""PDF 元素提取：文本和图片。"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import List, Literal, Optional, Union

import fitz

from pdf_tools.core import ExtractedImage, TextBlock


def extract_text_plain(
    doc: fitz.Document,
    pages: Optional[List[int]] = None,
) -> str:
    """提取纯文本内容。

    多页之间以两个换行符分隔。
    注意：若返回空字符串，可能该 PDF 为扫描版（纯图片，无文本层），
    需使用 OCR 技能处理。
    注意：pages=None 时提取全部页面，超大 PDF（数百页以上）可能占用大量内存，
    建议使用 pages 参数分页提取。
    不插入页码分隔标记，如需页码信息请使用 extract_text_blocks。

    Args:
        pages: 要提取的页码列表（1-based），None 表示全部页面

    Returns:
        str: 合并后的纯文本字符串
    """
    page_indices = _resolve_pages(doc, pages)
    texts: List[str] = []

    for p in page_indices:
        page_text = doc[p - 1].get_text()
        texts.append(page_text)  # 空字符串也加入，保留页码位置

    return "\n\n".join(texts)


def extract_text_blocks(
    doc: fitz.Document,
    pages: Optional[List[int]] = None,
) -> List[TextBlock]:
    """提取结构化文本块（带坐标和尺寸）。

    使用 PyMuPDF 的 get_text("blocks") 模式，每个块包含位置和文本内容。
    block_type 可能值为 0（text）、1（image）、2（struct）、3（vector）。
    返回顺序为 PyMuPDF 内部提取顺序（通常从上到下、从左到右），
    对于复杂排版（多栏、RTL、竖排）可能与视觉阅读顺序不一致。
    注意：blocks 模式不提供字体和字号信息（这些是 span 级别的细粒度数据，
    如需字体信息需改用 get_text("dict") 模式遍历，会显著增加复杂度）。

    Args:
        pages: 要提取的页码列表（1-based），None 表示全部页面

    Returns:
        List[TextBlock]: 文本块列表，按页面和阅读顺序排列
    """
    page_indices = _resolve_pages(doc, pages)
    blocks: List[TextBlock] = []

    for p in page_indices:
        page = doc[p - 1]
        raw_blocks = page.get_text("blocks")
        for item in raw_blocks:
            # item 格式: (x0, y0, x1, y1, text, block_no, block_type)
            x0, y0, x1, y1, text, _, block_type = item
            blocks.append(
                TextBlock(
                    page=p,
                    text=text,
                    x=x0,
                    y=y0,
                    width=x1 - x0,
                    height=y1 - y0,
                    block_type=block_type,
                )
            )

    return blocks


def extract_images(
    doc: fitz.Document,
    pages: Optional[List[int]] = None,
    output_mode: Literal["files", "base64"] = "files",
    output_dir: Optional[Union[str, Path]] = None,
) -> List[ExtractedImage]:
    """提取 PDF 中嵌入的位图图片（XObject Image）。

    仅提取位图嵌入，不包含矢量图形（路径绘制的图形、嵌入 SVG）。
    ext 字段优先使用 PyMuPDF 返回的格式，不可靠时根据像素格式回退推断。
    若推断失败，回退为 png。
    ExtractedImage.index 为全局索引（跨所有页面连续编号，从 0 开始）。

    Args:
        pages: 要提取的页码列表（1-based），None 表示全部页面
        output_mode: "files" 保存到 output_dir 并返回文件路径；"base64" 返回 base64 编码数据
        output_dir: output_mode="files" 时必填，指定输出目录

    Raises:
        ValueError: output_mode="files" 但 output_dir 为 None 时抛出

    Returns:
        List[ExtractedImage]

    Warning:
        base64 模式对大图片（如扫描版 PDF 的全页图片）会产生巨大的 base64 字符串，
        可能导致内存问题和 JSON 输出过大。建议仅用于小图片（图标、插图）。
    """
    if output_mode == "files" and output_dir is None:
        raise ValueError("output_mode='files' 时必须提供 output_dir")

    if output_mode == "files":
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    page_indices = _resolve_pages(doc, pages)
    images: List[ExtractedImage] = []
    img_index = 0

    for p in page_indices:
        page = doc[p - 1]
        img_list = page.get_images(full=True)
        for img_info in img_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)

                if base_image is None:
                    continue

                ext = base_image["ext"]
                image_bytes = base_image["image"]
                width = base_image["width"]
                height = base_image["height"]

                # ext 回退处理
                if not ext or ext.lower() == "n/a":
                    ext = _infer_image_ext(base_image)

                if output_mode == "files":
                    output_path = Path(output_dir) / f"img_{img_index:04d}.{ext}"
                    output_path.write_bytes(image_bytes)
                    images.append(
                        ExtractedImage(
                            page=p,
                            index=img_index,
                            width=width,
                            height=height,
                            ext=ext,
                            path=str(output_path),
                        )
                    )
                else:  # base64
                    b64 = base64.b64encode(image_bytes).decode("ascii")
                    images.append(
                        ExtractedImage(
                            page=p,
                            index=img_index,
                            width=width,
                            height=height,
                            ext=ext,
                            base64_data=b64,
                        )
                    )

                img_index += 1

    return images


def _infer_image_ext(base_image: dict) -> str:
    """根据像素格式推断图片扩展名。

    Args:
        base_image: doc.extract_image() 返回的字典

    Returns:
        推断的图片扩展名（png 或 jpeg）
    """
    # PyMuPDF 的 extract_image 返回的 mask 信息
    # 根据通道数推断格式
    # 注意：我们无法直接获取通道数，但可以通过 ext 回退
    # 更可靠的方式是尝试通过 colorspace 推断
    colorspace = base_image.get("colorspace", 0)

    # colorspace 值参考：
    # 1 = gray, 3 = rgb, 4 = cmyk
    # 保守策略：RGB 可能带 alpha 通道（RGBA），jpeg 不支持 alpha，
    # 因此对所有不确定情况回退为 png，确保兼容性
    if colorspace == 1:
        return "png"  # 灰度 -> png
    elif colorspace == 3:
        return "png"  # RGB -> png（可能含 alpha，保守处理）
    elif colorspace == 4:
        return "png"  # CMYK -> png

    # 默认回退
    return "png"


def _resolve_pages(doc: fitz.Document, pages: Optional[List[int]]) -> List[int]:
    """将用户传入的页码列表解析为有效的 1-based 页码列表。

    Args:
        doc: PDF Document
        pages: 用户指定的页码列表，None 表示全部页面

    Returns:
        List[int]: 1-based 页码列表
    """
    if pages is None:
        return list(range(1, doc.page_count + 1))
    return pages
