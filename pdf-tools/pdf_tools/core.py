"""pdf-tools 共享基础设施：PDF 打开/校验/类型定义/工具函数。"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union

import fitz


# ---------------------------------------------------------------------------
# 类型定义
# ---------------------------------------------------------------------------

@dataclass
class MetadataInfo:
    """PDF 元数据信息。"""

    page_count: int
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]  # ISO 8601 格式
    modification_date: Optional[str]
    pdf_version: str


@dataclass
class TextBlock:
    """文本块，坐标使用 top-left 像素坐标系。

    原点在页面左上角，x 向右增长，y 向下增长。
    坐标为绝对像素值（非归一化），与页面尺寸对应。
    PyMuPDF 的 get_text("blocks") 返回的坐标已经是此坐标系，无需额外转换。
    """

    page: int
    text: str
    x: float
    y: float
    width: float
    height: float
    block_type: int  # 0=text, 1=image, 2=struct, 3=vector


@dataclass
class ExtractedImage:
    """提取的图片信息。path 与 base64_data 恰好一个非 None。"""

    page: int
    index: int
    width: int
    height: int
    ext: str
    path: Optional[str] = None
    base64_data: Optional[str] = None


# ---------------------------------------------------------------------------
# PDF 打开/校验
# ---------------------------------------------------------------------------

@contextmanager
def open_pdf(
    path: Union[str, Path],
    password: Optional[str] = None,
) -> Generator[fitz.Document, None, None]:
    """以上下文管理器方式打开并校验 PDF 文件。

    校验项：文件存在、可读、是有效 PDF、非加密或密码正确。
    退出上下文时自动关闭 Document，避免资源泄漏。

    Args:
        path: PDF 文件路径
        password: PDF 打开密码（若文件加密则必需）

    Raises:
        FileNotFoundError: 文件不存在（不包装，直接抛出）
        PermissionError: 无读取权限（不包装，直接抛出）
        ValueError: 文件损坏/非有效 PDF，或密码错误/缺失
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在：{path_obj}")
    if not path_obj.is_file():
        raise ValueError(f"路径不是文件：{path_obj}")
    if not os.access(path_obj, os.R_OK):
        raise PermissionError(f"无读取权限：{path_obj}")

    doc: fitz.Document | None = None
    try:
        doc = fitz.open(str(path_obj))
    except fitz.FileDataError as e:
        raise ValueError(f"文件损坏或不是有效的 PDF：{path_obj}") from e
    except Exception as e:
        # 其他 fitz.open 异常统一包装
        raise ValueError(f"无法打开 PDF 文件：{path_obj}") from e

    # 检查是否加密
    if doc.is_encrypted:
        if password is None:
            doc.close()
            raise ValueError(f"PDF 文件已加密，需要提供密码：{path_obj}")
        auth_result = doc.authenticate(password)
        if auth_result == 0:
            doc.close()
            raise ValueError(f"PDF 密码错误：{path_obj}")

    try:
        yield doc
    finally:
        if doc is not None and not doc.is_closed:
            doc.close()


@contextmanager
def open_documents(
    paths: List[Union[str, Path]],
    password: Optional[str] = None,
) -> Generator[List[fitz.Document], None, None]:
    """以上下文管理器方式批量打开多个 PDF 文件。

    用于 merge_pdfs 等需要同时打开多个源文件的场景。
    退出上下文时自动关闭所有 Document。

    Args:
        paths: PDF 文件路径列表
        password: 打开密码（所有文件共用同一密码）

    Raises:
        FileNotFoundError: 某个文件不存在时抛出（不包装）
        PermissionError: 某个文件无权限时抛出（不包装）
        ValueError: 某个文件损坏/加密/非有效 PDF 时抛出
    """
    docs: List[fitz.Document] = []
    try:
        for p in paths:
            with open_pdf(p, password=password) as doc:
                docs.append(doc)
        yield docs
    finally:
        for doc in docs:
            if not doc.is_closed:
                doc.close()
