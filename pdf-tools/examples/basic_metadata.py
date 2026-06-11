"""示例：查看 PDF 元数据。"""

from pathlib import Path

from pdf_tools import get_metadata, open_pdf

pdf_path = Path("document.pdf")

with open_pdf(pdf_path) as doc:
    meta = get_metadata(doc)

print(f"页数: {meta.page_count}")
print(f"标题: {meta.title}")
print(f"作者: {meta.author}")
print(f"创建日期: {meta.creation_date}")
print(f"PDF 版本: {meta.pdf_version}")
