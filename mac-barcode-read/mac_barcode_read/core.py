"""macOS 单图条码读取核心能力。"""

from __future__ import annotations

import os
import platform
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image

Region = tuple[float, float, float, float]
"""归一化矩形 (x, y, w, h)。对外 API 使用左上角原点（top-left）。"""

DEFAULT_BARCODE_TYPES: frozenset[str] = frozenset(
    {
        "ean8",
        "ean13",
        "upce",
        "code39",
        "code93",
        "code128",
        "itf",
        "codabar",
        "qrcode",
    }
)

_BARCODE_TYPE_TO_VISION_SYMBOLS: dict[str, tuple[str, ...]] = {
    "ean8": ("VNBarcodeSymbologyEAN8",),
    "ean13": ("VNBarcodeSymbologyEAN13",),
    "upce": ("VNBarcodeSymbologyUPCE",),
    "code39": ("VNBarcodeSymbologyCode39", "VNBarcodeSymbologyCode39Checksum"),
    "code93": ("VNBarcodeSymbologyCode93",),
    "code128": ("VNBarcodeSymbologyCode128",),
    "itf": ("VNBarcodeSymbologyI2of5", "VNBarcodeSymbologyITF14"),
    "codabar": ("VNBarcodeSymbologyCodabar",),
    "qrcode": ("VNBarcodeSymbologyQR",),
}


class VisionBackendUnavailableError(ImportError):
    """Vision 后端不可用错误。"""


def _is_backend_unavailable_error_text(message: str) -> bool:
    normalized = message.lower()
    markers = (
        "check process entitlements",
        "could not create/add network to inference plan",
        "espresso exception",
        "unable to create request handler",
        "vision framework unavailable",
        "backend unavailable",
    )
    return any(marker in normalized for marker in markers)


def _load_vision_dependencies() -> tuple[Any, Any, Any, Any, Any]:
    """延迟导入 Vision 相关依赖，便于非 Darwin 环境单测。"""
    if platform.system() != "Darwin":
        raise ImportError("Vision 条码识别仅支持 Darwin/macOS 环境")
    try:
        import Vision  # type: ignore[import-not-found]
        from Foundation import NSURL  # type: ignore[import-not-found]
        from Quartz import (  # type: ignore[import-not-found]
            CGImageSourceCopyPropertiesAtIndex,
            CGImageSourceCreateWithURL,
            kCGImagePropertyPixelHeight,
            kCGImagePropertyPixelWidth,
        )
    except Exception as exc:  # pragma: no cover - 依赖错误通常受环境影响
        raise ImportError(
            "Vision 依赖不可用，请安装 pyobjc 相关组件（Vision/Foundation/Quartz）"
        ) from exc
    return (
        Vision,
        NSURL,
        CGImageSourceCreateWithURL,
        CGImageSourceCopyPropertiesAtIndex,
        (kCGImagePropertyPixelWidth, kCGImagePropertyPixelHeight),
    )


def _load_image_size_and_url(
    *,
    image_path: Path,
    ns_url_cls: Any,
    create_image_source: Any,
    copy_props_at_index: Any,
    prop_keys: tuple[Any, Any],
) -> tuple[int, int, Any]:
    """读取图片像素尺寸并返回 NSURL。"""
    ns_url = ns_url_cls.fileURLWithPath_(str(image_path))
    image_source = create_image_source(ns_url, None)
    if image_source is None:
        raise ValueError(f"无法加载图片：{image_path}")

    properties = copy_props_at_index(image_source, 0, None) or {}
    width_key, height_key = prop_keys
    width = int(properties.get(width_key, 0))
    height = int(properties.get(height_key, 0))
    if width <= 0 or height <= 0:
        raise ValueError(f"无法读取图片尺寸：{image_path}")
    return width, height, ns_url


def _resolve_vision_symbologies(
    *,
    vision_module: Any,
    selected_types: set[str],
    is_explicit_barcode_types: bool,
) -> list[Any]:
    """将统一 barcode_type 映射到 Vision symbology 常量。"""
    resolved: list[Any] = []
    for barcode_type in sorted(selected_types):
        symbol_names = _BARCODE_TYPE_TO_VISION_SYMBOLS.get(barcode_type, ())
        available = [getattr(vision_module, name, None) for name in symbol_names]
        available = [item for item in available if item is not None]
        if not available and is_explicit_barcode_types:
            raise ValueError(f"当前系统不支持 barcode_type: {barcode_type}")
        resolved.extend(available)
    return resolved


def _normalize_symbology(raw_symbology: Any) -> str:
    """将 Vision symbology 标识规范化为 barcode_type。"""
    symbology = str(raw_symbology or "").strip().lower()
    if not symbology:
        return ""
    if "qr" in symbology:
        return "qrcode"
    if "ean13" in symbology or "ean-13" in symbology:
        return "ean13"
    if "ean8" in symbology or "ean-8" in symbology:
        return "ean8"
    if "upce" in symbology or "upc-e" in symbology:
        return "upce"
    if "code128" in symbology or "code-128" in symbology:
        return "code128"
    if "code93" in symbology or "code-93" in symbology:
        return "code93"
    if "code39" in symbology or "code-39" in symbology:
        return "code39"
    if "i2of5" in symbology or "interleaved2of5" in symbology or "itf" in symbology:
        return "itf"
    if "codabar" in symbology:
        return "codabar"
    return "".join(ch for ch in symbology if ch.isalnum() or ch == "_")


def _vision_y_to_top_left_y(y_vision: float, h: float) -> float:
    """Vision 归一化 y（左下角原点）转为 top-left 归一化 y。"""
    return 1.0 - (float(y_vision) + float(h))


def _top_left_y_to_vision_y(y_top: float, h: float) -> float:
    """top-left 归一化 y 转为 Vision regionOfInterest / boundingBox 的 y。"""
    return 1.0 - (float(y_top) + float(h))


def _region_top_left_to_vision(region: Region) -> Region:
    """将 top-left 归一化区域转为 Vision ROI（左下角原点）。"""
    x, y, w, h = region
    return (float(x), _top_left_y_to_vision_y(y, h), float(w), float(h))


def _bbox_vision_to_top_left_xywh(x: float, y_vision: float, w: float, h: float) -> list[float]:
    """Vision 归一化 bbox 转为对外 top-left [x, y, w, h]。"""
    return [float(x), _vision_y_to_top_left_y(y_vision, h), float(w), float(h)]


def _bbox_to_xywh(bbox: Any) -> list[float]:
    """将 Vision boundingBox 统一为对外 top-left 归一化 [x, y, w, h]。"""
    if hasattr(bbox, "origin") and hasattr(bbox, "size"):
        x = float(getattr(bbox.origin, "x", 0.0))
        y = float(getattr(bbox.origin, "y", 0.0))
        w = float(getattr(bbox.size, "width", 0.0))
        h = float(getattr(bbox.size, "height", 0.0))
        return _bbox_vision_to_top_left_xywh(x, y, w, h)

    if isinstance(bbox, Sequence) and len(bbox) == 2:
        origin, size = bbox
        if (
            isinstance(origin, Sequence)
            and len(origin) == 2
            and isinstance(size, Sequence)
            and len(size) == 2
        ):
            x, y = origin
            w, h = size
            return _bbox_vision_to_top_left_xywh(float(x), float(y), float(w), float(h))

    if isinstance(bbox, Sequence) and len(bbox) == 4:
        x, y, w, h = bbox
        return _bbox_vision_to_top_left_xywh(float(x), float(y), float(w), float(h))

    return [0.0, 0.0, 0.0, 0.0]


def _detect_raw_codes(
    *,
    vision_module: Any,
    handler: Any,
    region: Region,
    allowed_symbologies: Sequence[Any],
) -> list[dict[str, Any]]:
    """在单个 top-left 归一化区域内执行 Vision 检测，返回原始结果列表。"""
    request = vision_module.VNDetectBarcodesRequest.alloc().init()
    if allowed_symbologies:
        request.setSymbologies_(list(allowed_symbologies))
    vision_region = _region_top_left_to_vision(region)
    request.setRegionOfInterest_(
        ((vision_region[0], vision_region[1]), (vision_region[2], vision_region[3]))
    )

    try:
        perform_result = handler.performRequests_error_([request], None)
    except Exception as exc:
        message = str(exc)
        if _is_backend_unavailable_error_text(message):
            raise VisionBackendUnavailableError(f"Vision 后端不可用：{message}") from exc
        raise
    if isinstance(perform_result, tuple):
        success = bool(perform_result[0])
        error = perform_result[1]
    else:
        success = bool(perform_result)
        error = None
    if not success:
        message = str(error)
        if _is_backend_unavailable_error_text(message):
            raise VisionBackendUnavailableError(f"Vision 后端不可用：{message}")
        raise RuntimeError(f"Vision 条码检测失败：{message}")

    results = request.results() or []
    raw_codes: list[dict[str, Any]] = []
    for item in results:
        confidence = float(item.confidence()) if hasattr(item, "confidence") else None
        raw_codes.append(
            {
                "payload_string_value": item.payloadStringValue()
                if hasattr(item, "payloadStringValue")
                else "",
                "symbology": _normalize_symbology(item.symbology()) if hasattr(item, "symbology") else "",
                "bbox": _bbox_to_xywh(item.boundingBox()) if hasattr(item, "boundingBox") else [0.0, 0.0, 0.0, 0.0],
                "confidence": confidence,
            }
        )
    return raw_codes


def _passes_confidence(code: Mapping[str, Any], min_confidence: float) -> bool:
    """判断条码是否满足最小置信度阈值。"""
    confidence = code.get("confidence")
    if confidence is None:
        return min_confidence <= 0.0
    try:
        return float(confidence) >= min_confidence
    except (TypeError, ValueError):
        return False


def normalize_and_validate_barcode_types(
    barcode_types: Sequence[str] | None,
) -> set[str]:
    """规范化并校验 barcode_type 集合。"""
    if barcode_types is None:
        return set(DEFAULT_BARCODE_TYPES)

    normalized = {item.strip().lower() for item in barcode_types if item and item.strip()}
    if not normalized:
        return set(DEFAULT_BARCODE_TYPES)

    unknown = normalized - DEFAULT_BARCODE_TYPES
    if unknown:
        raise ValueError(f"不支持的 barcode_type: {', '.join(sorted(unknown))}")
    return normalized


def filter_codes_by_type(
    codes: Sequence[Mapping[str, Any]],
    allowed: set[str] | None,
) -> list[dict[str, Any]]:
    """按 barcode_type 过滤识别结果。"""
    normalized_codes = [dict(item) for item in codes]
    if not allowed:
        return normalized_codes
    return [item for item in normalized_codes if item.get("barcode_type") in allowed]


def map_raw_code(raw_code: Mapping[str, Any]) -> dict[str, Any]:
    """将底层原始识别结果映射为统一输出字段。"""
    value = raw_code.get("value")
    if value is None:
        value = raw_code.get("payload_string_value")
    if value is None:
        value = raw_code.get("payloadStringValue")
    if value is None:
        value = ""

    raw_type = raw_code.get("barcode_type")
    if raw_type is None:
        raw_type = raw_code.get("symbology", "")
    barcode_type = str(raw_type).strip().lower()

    bbox = raw_code.get("bbox")
    if not isinstance(bbox, Sequence) or len(bbox) != 4:
        bbox = raw_code.get("bounding_box", raw_code.get("boundingBox", (0.0, 0.0, 0.0, 0.0)))
    if isinstance(bbox, Sequence) and len(bbox) == 4:
        bbox_values = [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
    else:
        bbox_values = [0.0, 0.0, 0.0, 0.0]

    confidence = raw_code.get("confidence")
    return {
        "value": str(value),
        "barcode_type": barcode_type,
        "bbox": bbox_values,
        "confidence": float(confidence) if confidence is not None else None,
    }


def _validate_normalized_region(region: Region) -> None:
    """校验归一化区域值合法性。"""
    x, y, w, h = region
    if any(value < 0 or value > 1 for value in (x, y, w, h)):
        raise ValueError("region 值必须在 [0,1] 范围内")
    if w <= 0 or h <= 0:
        raise ValueError("region 的宽高必须大于 0")
    if x + w > 1 or y + h > 1:
        raise ValueError("region 超出图像边界")


def _normalize_single_region(
    region: Region,
    *,
    width: int,
    height: int,
) -> Region:
    """将单个区域按规格归一化为 top-left 坐标（不翻转 y 轴）。"""
    x, y, w, h = region
    x_norm = x / width if x >= 1 else x
    y_norm = y / height if y >= 1 else y
    w_norm = w / width if w > 1 else w
    h_norm = h / height if h > 1 else h

    normalized = (float(x_norm), float(y_norm), float(w_norm), float(h_norm))
    _validate_normalized_region(normalized)
    return normalized


def normalize_regions(
    regions: Sequence[Region] | None,
    *,
    width: int,
    height: int,
) -> list[Region]:
    """归一化区域列表为 top-left 坐标；未提供时返回整图区域。

    返回值可直接用于对外 API；传入 Vision 前需经 `_region_top_left_to_vision` 转换。
    """
    source_regions: Sequence[Region] = regions or ((0.0, 0.0, 1.0, 1.0),)
    return [
        _normalize_single_region(region, width=width, height=height)
        for region in source_regions
    ]


def _pil_image_to_cgimage(image: Image.Image) -> Any:
    """将 PIL Image 转为 Quartz CGImage（纯内存，无磁盘 I/O）。"""
    import Quartz  # type: ignore[import-not-found]
    from Foundation import NSData  # type: ignore[import-not-found]

    if image.mode != "RGBA":
        image = image.convert("RGBA")
    width, height = image.size
    raw = image.tobytes()

    data = NSData.dataWithBytes_length_(raw, len(raw))
    provider = Quartz.CGDataProviderCreateWithCFData(data)
    colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
    bitmap_info = getattr(Quartz, "kCGImageAlphaLast", Quartz.kCGImageAlphaPremultipliedLast)

    cgimage = Quartz.CGImageCreate(
        width, height,
        8, 32,
        width * 4,
        colorspace,
        bitmap_info,
        provider,
        None,
        False,
        Quartz.kCGRenderingIntentDefault,
    )
    return cgimage


def _load_image(
    image: str | Path | bytes | Image.Image,
) -> tuple[Image.Image, Path | None]:
    """统一加载图像，返回 (PIL Image, 文件路径或 None)。

    Raises:
        FileNotFoundError: 路径不存在。
        ValueError: 类型不支持。
    """
    if isinstance(image, (str, Path)):
        path = Path(image).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"图片文件不存在或不是文件：{image}")
        with Image.open(path) as im:
            return im.convert("RGB"), path

    if isinstance(image, bytes):
        return Image.open(BytesIO(image)).convert("RGB"), None

    if isinstance(image, Image.Image):
        return image.convert("RGB"), None

    raise ValueError("image 必须是 str/Path/bytes/PIL.Image.Image")


def build_success_payload(
    *,
    image_path: str | None,
    codes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """构建成功响应载荷。"""
    normalized_codes = [dict(item) for item in codes]
    return {
        "success": True,
        "data": {
            "image_path": image_path,
            "codes": normalized_codes,
        },
    }


def read_barcodes_from_image(
    image: str | Path | bytes | Image.Image,
    *,
    regions: Sequence[tuple[float, float, float, float]] | None = None,
    barcode_types: Sequence[str] | None = None,
    max_results: int | None = None,
    min_confidence: float = 0.0,
) -> dict[str, Any]:
    """读取图片中的条码并返回统一结构。

    Args:
        image: 输入图像，支持路径、bytes、PIL.Image.Image。
        regions: 识别区域列表，元素为 ``(x, y, w, h)``（top-left 归一化或像素/比例混合）。
            ``None`` 或空序列表示整图。
        barcode_types: 条码类型过滤条件。
        max_results: 限制返回条码数量；``None`` 表示不限制。
        min_confidence: 最小置信度阈值（0~1）。

    Returns:
        dict[str, Any]: 识别结果，包含 ``image_path``（内存输入时为 ``None``）和 ``codes``。

    Raises:
        FileNotFoundError: 路径不存在或不是文件。
        ValueError: 参数非法或图像类型不支持。
        ImportError: Vision 依赖不可用或非 macOS 环境。
    """
    img_obj, source_path = _load_image(image)

    if min_confidence < 0 or min_confidence > 1:
        raise ValueError("min_confidence 必须在 [0,1] 范围内")
    if max_results is not None and max_results < 1:
        raise ValueError("max_results 传入时必须大于 0")
    if regions is not None and len(regions) == 0:
        regions = None
    if barcode_types is not None and len(barcode_types) == 0:
        barcode_types = None

    selected_types = normalize_and_validate_barcode_types(barcode_types)
    (
        vision_module,
        ns_url_cls,
        create_image_source,
        copy_props_at_index,
        prop_keys,
    ) = _load_vision_dependencies()

    if source_path is not None:
        width, height, image_url = _load_image_size_and_url(
            image_path=source_path,
            ns_url_cls=ns_url_cls,
            create_image_source=create_image_source,
            copy_props_at_index=copy_props_at_index,
            prop_keys=prop_keys,
        )
        handler = vision_module.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
    else:
        width, height = img_obj.size
        cgimage = _pil_image_to_cgimage(img_obj)
        handler = vision_module.VNImageRequestHandler.alloc().initWithCGImage_options_(cgimage, None)

    normalized_regions = normalize_regions(regions=regions, width=width, height=height)
    allowed_symbologies = _resolve_vision_symbologies(
        vision_module=vision_module,
        selected_types=selected_types,
        is_explicit_barcode_types=barcode_types is not None,
    )

    raw_codes: list[dict[str, Any]] = []
    for region in normalized_regions:
        raw_codes.extend(
            _detect_raw_codes(
                vision_module=vision_module,
                handler=handler,
                region=region,
                allowed_symbologies=allowed_symbologies,
            )
        )

    mapped_codes = [map_raw_code(item) for item in raw_codes]
    type_filtered_codes = filter_codes_by_type(mapped_codes, selected_types)
    confidence_filtered_codes = [
        item for item in type_filtered_codes if _passes_confidence(item, min_confidence)
    ]
    if max_results is not None:
        confidence_filtered_codes = confidence_filtered_codes[:max_results]

    return {
        "image_path": str(source_path) if source_path is not None else None,
        "codes": confidence_filtered_codes,
    }


def recognize_barcodes(
    image: str | Path | bytes | Image.Image,
    *,
    regions: Sequence[tuple[float, float, float, float]] | None = None,
    barcode_types: Sequence[str] | None = None,
    max_results: int | None = None,
    min_confidence: float = 0.0,
) -> dict[str, Any]:
    """read_barcodes_from_image 的语义别名。"""
    return read_barcodes_from_image(
        image,
        regions=regions,
        barcode_types=barcode_types,
        max_results=max_results,
        min_confidence=min_confidence,
    )
