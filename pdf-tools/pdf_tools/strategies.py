"""PDF 图片提取 fallback 策略工厂。"""

from __future__ import annotations

from typing import List

import fitz

from pdf_tools.core import PageFallback


def too_many_small_elements(
    max_size_ratio: float = 0.5,
    min_count: int = 2,
) -> PageFallback:
    """创建"小图片过多则渲染"策略。

    当页面上面积不超过页面指定比例的图片实例数量严格大于阈值时返回 True，
    调用方应将该页渲染为图片而非提取嵌入图片。

    使用 page.get_image_rects 获取每张图片在页面上的实际占用区域，可处理
    get_text("blocks") 无法识别内容块的扫描/图片型 PDF。

    Args:
        max_size_ratio: 小图片判定阈值，表示图片面积占页面面积的最大比例。
            例如 0.5 表示面积不超过半页的图片被视为小图片。
        min_count: 小图片数量阈值。当小图片数量严格大于该值时返回 True。

    Returns:
        PageFallback: 判断函数，接收 fitz.Page 并返回 bool。
    """
    def decide(page: fitz.Page) -> bool:
        page_area = page.rect.width * page.rect.height
        img_list = page.get_images(full=True)

        small_count = 0
        for img_info in img_list:
            xref = img_info[0]
            rects = page.get_image_rects(xref)
            for rect in rects:
                area = rect.width * rect.height
                if area / page_area <= max_size_ratio:
                    small_count += 1

        return small_count > min_count

    return decide
