"""PDF 图片提取 fallback 策略工厂。"""

from __future__ import annotations

from typing import List

import fitz

from pdf_tools.core import PageFallback


def too_many_small_elements(
    max_size_ratio: float = 0.5,
    min_count: int = 3,
) -> PageFallback:
    """创建"小元素过多则渲染"策略。

    当页面中面积不超过页面指定比例的内容块数量严格大于阈值时返回 True，
    调用方应将该页渲染为图片而非提取嵌入图片。

    Args:
        max_size_ratio: 小元素判定阈值，表示元素面积占页面面积的最大比例。
            例如 0.5 表示面积不超过半页的元素被视为小元素。
        min_count: 小元素数量阈值。当小元素数量严格大于该值时返回 True。

    Returns:
        PageFallback: 判断函数，接收 fitz.Page 并返回 bool。
    """
    def decide(page: fitz.Page) -> bool:
        page_area = page.rect.width * page.rect.height
        blocks: List[tuple] = page.get_text("blocks")

        small_count = 0
        for b in blocks:
            area = (b[2] - b[0]) * (b[3] - b[1])
            if area / page_area <= max_size_ratio:
                small_count += 1

        return small_count > min_count

    return decide
