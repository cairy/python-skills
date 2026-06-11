"""pdf-tools — 跨平台 PDF 处理工具包。"""

from pdf_tools.core import (
    ExtractedImage,
    MetadataInfo,
    TextBlock,
    open_documents,
    open_pdf,
    parse_page_ranges,
)
from pdf_tools.extract import (
    extract_images,
    extract_text_blocks,
    extract_text_plain,
)
from pdf_tools.metadata import get_metadata
from pdf_tools.pages import merge_pdfs, rotate_pages, split_pages
from pdf_tools.render import RenderedPage, render_pages

__all__ = [
    "open_pdf",
    "open_documents",
    "parse_page_ranges",
    "MetadataInfo",
    "TextBlock",
    "ExtractedImage",
    "RenderedPage",
    "get_metadata",
    "split_pages",
    "merge_pdfs",
    "rotate_pages",
    "extract_text_plain",
    "extract_text_blocks",
    "extract_images",
    "render_pages",
]
