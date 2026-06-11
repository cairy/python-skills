"""示例：拆分和合并 PDF。"""

from pathlib import Path

from pdf_tools import merge_pdfs, open_pdf, split_pages

# 拆分：从多页 PDF 提取前 3 页
with open_pdf("input.pdf") as doc:
    split_pages(doc, pages=[1, 2, 3], output_path="first_three.pdf")

# 合并：将两个 PDF 合并为一个
merge_pdfs(
    input_paths=["a.pdf", "b.pdf"],
    output_path="merged.pdf",
)
