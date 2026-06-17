"""图片处理 pipeline：原子操作与编排。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from image_tools.annotate import draw_boxes
from image_tools.core import (
    BatchResult,
    Box,
    ImageFormat,
    ProcessResult,
    ResizeMode,
    validate_input_path,
    validate_output_dir,
)


def _open_image(path: str | Path) -> Image.Image:
    """打开图片并返回可独立使用的副本。"""
    with Image.open(path) as img:
        return img.copy()


def step_exif_transpose(image: Image.Image) -> Image.Image:
    """根据 EXIF Orientation 转正图片。"""
    return ImageOps.exif_transpose(image)


def step_resize(
    image: Image.Image,
    width: int,
    height: int,
    mode: ResizeMode = "fit-without-pad",
) -> Image.Image:
    """等比缩放图片。

    默认 fit-without-pad：按长边等比缩放，保持比例，不填充画布。
    """
    if width <= 0 or height <= 0:
        raise ValueError("缩放尺寸必须大于 0")

    if mode == "fit-without-pad":
        img_w, img_h = image.size
        ratio = min(width / img_w, height / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        if (new_w, new_h) != image.size:
            return image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return image

    if mode == "fit":
        img_w, img_h = image.size
        ratio = min(width / img_w, height / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), "white")
        offset_x = (width - new_w) // 2
        offset_y = (height - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y))
        return canvas

    if mode == "cover":
        return ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)

    raise ValueError(f"不支持的缩放模式：{mode}")


def _format_to_pil(fmt: str) -> str:
    """将用户格式名转换为 Pillow 保存格式名。"""
    fmt = fmt.lower()
    if fmt in ("jpg", "jpeg"):
        return "JPEG"
    mapping = {
        "png": "PNG",
        "webp": "WEBP",
    }
    if fmt in mapping:
        return mapping[fmt]
    raise ValueError(f"不支持的输出格式：{fmt}")


def _prepare_rgb(image: Image.Image, fmt: str) -> Image.Image:
    """根据目标格式准备颜色模式。"""
    fmt = fmt.lower()
    if fmt == "png":
        return image
    if image.mode in ("RGBA", "P"):
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        composite = Image.alpha_composite(background, image)
        return composite.convert("RGB")
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def step_convert(
    image: Image.Image,
    fmt: ImageFormat = "jpg",
    quality: int = 85,
    keep_exif: bool = False,
) -> tuple[Image.Image, dict[str, Any]]:
    """转换图片格式，返回处理后的图片和保存选项。"""
    if not 1 <= quality <= 100:
        raise ValueError("quality 必须在 1-100 之间")

    fmt = fmt.lower()  # type: ignore[assignment]
    prepared = _prepare_rgb(image, fmt)
    save_kwargs: dict[str, Any] = {}
    if fmt in ("jpg", "jpeg", "webp"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    if keep_exif:
        save_kwargs["exif"] = image.info.get("exif", b"")
    return prepared, save_kwargs


def step_compress(
    image: Image.Image,
    quality: int = 85,
    keep_exif: bool = False,
    fmt: str = "jpg",
) -> tuple[Image.Image, dict[str, Any]]:
    """重新编码压缩；输出格式由 fmt 参数决定（默认 jpg）。"""
    return step_convert(image, fmt=fmt, quality=quality, keep_exif=keep_exif)


def _save_image(
    image: Image.Image,
    output_path: str | Path,
    fmt: str,
    save_kwargs: dict[str, Any],
) -> None:
    """保存图片到指定路径。"""
    pil_format = _format_to_pil(fmt)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, pil_format, **save_kwargs)


def process_image(
    input_path: str | Path,
    output_path: str | Path,
    pipeline: list[str],
    width: int | None = None,
    height: int | None = None,
    format: str = "jpg",
    quality: int = 85,
    keep_exif: bool = False,
    boxes: list[Box] | None = None,
    resize_mode: ResizeMode = "fit-without-pad",
) -> ProcessResult:
    """处理单张图片。

    Args:
        input_path: 输入图片路径。
        output_path: 输出图片路径。
        pipeline: 原子操作列表。
        width: resize 目标宽度上限。
        height: resize 目标高度上限。
        format: 输出格式。
        quality: JPEG/WebP 质量。
        keep_exif: 是否保留 EXIF。
        boxes: 标注框列表（annotate 操作使用）。
        resize_mode: 缩放模式。

    Returns:
        ProcessResult: 处理结果。
    """
    validate_input_path(input_path)

    image = _open_image(input_path)
    save_kwargs: dict[str, Any] = {}

    for step in pipeline:
        if step == "exif-transpose":
            image = step_exif_transpose(image)
        elif step == "resize":
            if width is None or height is None:
                raise ValueError("resize 操作需要 --width 和 --height")
            image = step_resize(image, width, height, mode=resize_mode)
        elif step == "convert":
            image, save_kwargs = step_convert(
                image, fmt=format, quality=quality, keep_exif=keep_exif
            )
        elif step == "compress":
            image, save_kwargs = step_compress(image, quality=quality, keep_exif=keep_exif, fmt=format)
        elif step == "annotate":
            image = draw_boxes(image, boxes or [])
        else:
            raise ValueError(f"不支持的原子操作：{step}")

    if not save_kwargs:
        # If no convert/compress step, default to saving as-is in requested format
        image, save_kwargs = step_convert(
            image, fmt=format, quality=quality, keep_exif=keep_exif
        )

    output_path_obj = Path(output_path)
    if output_path_obj.exists() and output_path_obj.is_dir():
        raise ValueError(f"输出路径是目录：{output_path_obj}")

    _save_image(image, output_path, format, save_kwargs)

    out_w, out_h = image.size

    return ProcessResult(
        input_path=str(input_path),
        output_path=str(output_path),
        width=out_w,
        height=out_h,
        format=format.lower(),
        size_bytes=output_path_obj.stat().st_size,
    )
