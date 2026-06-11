"""示例：提取 PDF 中的文本和图片。"""

from pathlib import Path

from pdf_tools import (
    extract_images,
    extract_text_blocks,
    extract_text_plain,
    open_pdf,
)

with open_pdf("document.pdf") as doc:
    # 提取纯文本
    text = extract_text_plain(doc)
    print("=== 纯文本 ===")
    print(text)

    # 提取结构化文本块
    blocks = extract_text_blocks(doc)
    print("\n=== 文本块 ===")
    for b in blocks[:3]:
        print(f"  [{b.x:.1f}, {b.y:.1f}] {b.text[:50]}...")

    # 提取图片
    images = extract_images(doc, output_mode="files", output_dir=Path("./images"))
    print(f"\n提取了 {len(images)} 张图片")
