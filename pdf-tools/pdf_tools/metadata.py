"""PDF 元数据提取。"""

from __future__ import annotations

import fitz

from pdf_tools.core import MetadataInfo, parse_pdf_date


def get_metadata(doc: fitz.Document) -> MetadataInfo:
    """提取 PDF 的完整元数据信息。

    日期字段通过 core.parse_pdf_date() 转换为 ISO 8601。
    不包含每页详细尺寸信息（按设计决策精简）。

    Args:
        doc: 已打开的 PDF Document

    Returns:
        MetadataInfo: 包含页数、标题、作者、PDF 版本等核心字段。
    """
    meta = doc.metadata

    return MetadataInfo(
        page_count=doc.page_count,
        title=meta.get("title") or None,
        author=meta.get("author") or None,
        subject=meta.get("subject") or None,
        creator=meta.get("creator") or None,
        producer=meta.get("producer") or None,
        creation_date=parse_pdf_date(meta.get("creationDate")),
        modification_date=parse_pdf_date(meta.get("modDate")),
        pdf_version=doc.metadata.get("format", "PDF 1.4").removeprefix("PDF "),
    )
