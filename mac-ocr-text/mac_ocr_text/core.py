"""macOS OCR 核心能力（基于 ocrmac）。"""

from __future__ import annotations

import math
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, Sequence, TypedDict

from PIL import Image

try:
    from ocrmac.ocrmac import OCR
except Exception:  # pragma: no cover - 在非 macOS/缺依赖环境下允许导入模块本身
    OCR = None  # type: ignore[assignment]

Framework = Literal["vision", "livetext"]
RecognitionLevel = Literal["accurate", "fast"]
LivetextUnit = Literal["token", "line"]
RegionTuple = tuple[float, float, float, float]


class TextSegmentDict(TypedDict):
    """单段识别结果。"""

    text: str
    confidence: float | None
    bbox: list[float] | None


class RegionResultDict(TypedDict):
    """单个区域的识别结果。"""

    region_index: int
    box: list[float]
    plain_text: str
    segments: list[TextSegmentDict]


def recognize_image_text(
    image: str | Path | bytes | Image.Image,
    *,
    regions: Sequence[RegionTuple] | None = None,
    framework: Framework = "vision",
    recognition_level: RecognitionLevel = "accurate",
    languages: list[str] | None = None,
    confidence_threshold: float = 0.0,
    include_boxes: bool = True,
    livetext_unit: LivetextUnit = "token",
) -> dict[str, Any]:
    """识别单张图像文字并返回结构化结果。

    Args:
        image: 输入图像，支持路径、`bytes`、`PIL.Image.Image`。
        regions: 识别区域列表，元素为 `(x, y, w, h)`。`None` 或空序列表示整图。
        framework: OCR 后端。`vision` 为默认；`livetext` 用于 token/line 粒度。
        recognition_level: 仅 `vision` 生效。`accurate` 偏精度，`fast` 偏速度。
        languages: 语言偏好（BCP-47 列表），如 `["zh-Hans", "en"]`。
        confidence_threshold: 仅 `vision` 生效，过滤低置信度结果。
        include_boxes: 为 `True` 时输出 `segments[].bbox`；否则仅输出文本。
        livetext_unit: 仅 `livetext` 生效，`token` 或 `line`。

    Returns:
        dict[str, Any]: 结构化识别结果，包含 `regions`、`framework`、`resolved_path` 等字段。

    Raises:
        FileNotFoundError: 输入路径不存在或不是文件。
        ValueError: 参数类型、参数组合或区域数值非法。
        ImportError: 后端不可用（例如当前系统不支持 livetext）。
    """
    if OCR is None:
        raise ImportError("ocrmac 不可用：请在 macOS 环境安装并启用相关系统框架")
    _validate_common_parameters(
        framework=framework,
        recognition_level=recognition_level,
        confidence_threshold=confidence_threshold,
        livetext_unit=livetext_unit,
        languages=languages,
    )

    image_obj, resolved_path = _load_image(image)
    width, height = image_obj.size
    normalized_regions = _normalize_regions(regions=regions, width=width, height=height)

    region_outputs: list[RegionResultDict] = []
    for idx, region in enumerate(normalized_regions):
        crop = _crop_image_by_region(image_obj, region)
        ocr = OCR(
            crop,
            framework=framework,
            recognition_level=recognition_level,
            language_preference=languages,
            confidence_threshold=confidence_threshold,
            detail=include_boxes,
            unit=livetext_unit,
        )
        raw = ocr.recognize()
        segments = _to_segments(raw=raw, include_boxes=include_boxes)
        region_outputs.append(
            {
                "region_index": idx,
                "box": [float(v) for v in region],
                "plain_text": "\n".join(seg["text"] for seg in segments),
                "segments": segments,
            }
        )

    return {
        "resolved_path": resolved_path,
        "framework": framework,
        "recognition_level": recognition_level,
        "include_boxes": include_boxes,
        "regions": region_outputs,
    }


def _validate_common_parameters(
    *,
    framework: Framework,
    recognition_level: RecognitionLevel,
    confidence_threshold: float,
    livetext_unit: LivetextUnit,
    languages: list[str] | None,
) -> None:
    if framework not in ("vision", "livetext"):
        raise ValueError("framework 必须是 'vision' 或 'livetext'")
    if recognition_level not in ("accurate", "fast"):
        raise ValueError("recognition_level 必须是 'accurate' 或 'fast'")
    if livetext_unit not in ("token", "line"):
        raise ValueError("livetext_unit 必须是 'token' 或 'line'")
    if not isinstance(confidence_threshold, (int, float)):
        raise ValueError("confidence_threshold 必须是数值")
    if confidence_threshold < 0:
        raise ValueError("confidence_threshold 不能小于 0")
    if languages is not None:
        if not isinstance(languages, list) or not all(
            isinstance(item, str) and item.strip() for item in languages
        ):
            raise ValueError("languages 必须是非空字符串列表或 None")

    # 按 spec 要求，这里选择“显式报错”，避免参数被静默忽略。
    if framework == "livetext" and recognition_level != "accurate":
        raise ValueError("framework=livetext 时不支持 recognition_level，请使用默认值")
    if framework == "livetext" and confidence_threshold != 0.0:
        raise ValueError("framework=livetext 时不支持 confidence_threshold，请使用默认值 0.0")


def _load_image(image: str | Path | bytes | Image.Image) -> tuple[Image.Image, str | None]:
    if isinstance(image, (str, Path)):
        path = Path(image).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"图片文件不存在或不是文件：{image}")
        with Image.open(path) as im:
            return im.convert("RGB"), str(path)

    if isinstance(image, bytes):
        with Image.open(BytesIO(image)) as im:
            return im.convert("RGB"), None

    if isinstance(image, Image.Image):
        return image.convert("RGB"), None

    raise ValueError("image 必须是 str/Path/bytes/PIL.Image.Image")


def _normalize_regions(
    *,
    regions: Sequence[RegionTuple] | None,
    width: int,
    height: int,
) -> list[RegionTuple]:
    if width <= 0 or height <= 0:
        raise ValueError("图像宽高必须为正数")

    source = list(regions) if regions else [(0.0, 0.0, 1.0, 1.0)]
    normalized: list[RegionTuple] = []

    for idx, region in enumerate(source):
        if len(region) != 4:
            raise ValueError(f"第 {idx} 个区域必须是 4 元组 [x,y,w,h]")
        x, y, w, h = [float(v) for v in region]
        x_n = x / width if x >= 1 else x
        y_n = y / height if y >= 1 else y
        w_n = w / width if w > 1 else w
        h_n = h / height if h > 1 else h
        _validate_normalized_region(x=x_n, y=y_n, w=w_n, h=h_n, region_index=idx)
        normalized.append((x_n, y_n, w_n, h_n))
    return normalized


def _validate_normalized_region(
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    region_index: int,
) -> None:
    for name, value in (("x", x), ("y", y), ("w", w), ("h", h)):
        if value < 0 or value > 1:
            raise ValueError(f"第 {region_index} 个区域的 {name} 超出范围 [0,1]")
    if w <= 0 or h <= 0:
        raise ValueError(f"第 {region_index} 个区域的 w/h 必须大于 0")
    if x + w > 1:
        raise ValueError(f"第 {region_index} 个区域不合法：x+w 不能大于 1")
    if y + h > 1:
        raise ValueError(f"第 {region_index} 个区域不合法：y+h 不能大于 1")


def _crop_image_by_region(image: Image.Image, region: RegionTuple) -> Image.Image:
    x, y, w, h = region
    width, height = image.size
    x0 = max(0, min(width, math.floor(x * width)))
    y0 = max(0, min(height, math.floor(y * height)))
    x1 = max(0, min(width, math.ceil((x + w) * width)))
    y1 = max(0, min(height, math.ceil((y + h) * height)))

    if x1 <= x0:
        x1 = min(width, x0 + 1)
    if y1 <= y0:
        y1 = min(height, y0 + 1)
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"区域裁切后为空：{region}")
    return image.crop((x0, y0, x1, y1))


def _to_segments(raw: Any, *, include_boxes: bool) -> list[TextSegmentDict]:
    segments: list[TextSegmentDict] = []
    if include_boxes:
        for item in raw:
            text, conf, bbox = item
            segments.append(
                {
                    "text": str(text),
                    "confidence": float(conf),
                    "bbox": [float(v) for v in bbox],
                }
            )
        return segments

    for text in raw:
        segments.append({"text": str(text), "confidence": None, "bbox": None})
    return segments
