"""PDF 页面操作：拆分、合并、旋转。"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

import fitz

from pdf_tools.core import open_documents, open_pdf


def split_pages(
    doc: fitz.Document,
    pages: List[int],
    output_path: Union[str, Path],
) -> str:
    """提取指定页面为新 PDF。

    Args:
        doc: 已打开的 PDF Document
        pages: 要提取的页码列表（1-based）
        output_path: 输出文件路径

    Raises:
        ValueError: pages 为空列表时抛出

    Returns:
        str: 输出文件路径
    """
    if not pages:
        raise ValueError("pages 不能为空列表")

    for p in pages:
        if p < 1 or p > doc.page_count:
            raise ValueError(f"页码越界（最大 {doc.page_count}）：{p}")

    output_path = Path(output_path)
    new_doc = fitz.open()

    try:
        for p in pages:
            new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        new_doc.save(str(output_path))
    finally:
        new_doc.close()

    return str(output_path)


def merge_pdfs(
    input_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
) -> str:
    """合并多个 PDF 为一个文件。

    按 input_paths 顺序合并。合并后的 PDF 保留各源文件的原始页面尺寸，不强制统一。
    若某个源文件加密，需先解密后再传入（本函数不处理密码）。

    Args:
        input_paths: 要合并的 PDF 文件路径列表
        output_path: 输出文件路径

    Raises:
        ValueError: input_paths 为空列表时抛出
        FileNotFoundError: 某个文件不存在时抛出（由 core.open_pdf 透传）
        PermissionError: 某个文件无权限时抛出（由 core.open_pdf 透传）
        ValueError: 某个文件损坏时抛出（由 core.open_pdf 透传）

    Returns:
        str: 输出文件路径
    """
    if not input_paths:
        raise ValueError("input_paths 不能为空列表")

    output_path = Path(output_path)
    new_doc = fitz.open()

    try:
        with open_documents(input_paths) as docs:
            for src_doc in docs:
                new_doc.insert_pdf(src_doc)
        new_doc.save(str(output_path))
    finally:
        new_doc.close()

    return str(output_path)


def rotate_pages(
    doc: fitz.Document,
    output_path: Union[str, Path],
    pages: List[int],
    angle: int,
) -> str:
    """旋转指定页面。

    仅旋转指定页码，其他页面保持不变。
    angle 限制为 PDF 标准旋转值（0/90/180/270），非法值抛出 ValueError。

    Args:
        doc: 已打开的 PDF Document
        output_path: 输出文件路径
        pages: 要旋转的页码列表（1-based）
        angle: 旋转角度，必须是 0、90、180 或 270

    Raises:
        ValueError: angle 不在 {0, 90, 180, 270} 中

    Returns:
        str: 输出文件路径
    """
    if angle not in {0, 90, 180, 270}:
        raise ValueError(f"旋转角度必须是 0、90、180 或 270，得到：{angle}")

    for p in pages:
        if p < 1 or p > doc.page_count:
            raise ValueError(f"页码越界（最大 {doc.page_count}）：{p}")

    output_path = Path(output_path)
    new_doc = fitz.open()

    try:
        new_doc.insert_pdf(doc)
        for p in pages:
            new_doc[p - 1].set_rotation(angle)
        new_doc.save(str(output_path))
    finally:
        new_doc.close()

    return str(output_path)
