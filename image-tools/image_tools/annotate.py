"""图片调试标注：在图片上绘制矩形框。"""

from __future__ import annotations

from PIL import Image, ImageDraw

from image_tools.core import Box


DEFAULT_COLORS: dict[str, str] = {
    "face": "red",
    "barcode": "blue",
    "group": "green",
}


def draw_boxes(image: Image.Image, boxes: list[Box]) -> Image.Image:
    """在图片副本上绘制矩形框。

    Args:
        image: 待标注图片。
        boxes: 标注框列表。

    Returns:
        带标注框的图片副本。
    """
    out = image.copy()
    draw = ImageDraw.Draw(out)
    for box in boxes:
        color = box.color or DEFAULT_COLORS.get(box.name, "yellow")
        draw.rectangle(
            [
                box.x,
                box.y,
                box.x + box.width,
                box.y + box.height,
            ],
            outline=color,
            width=3,
        )
    return out
