"""macOS 单图条码读取核心能力。"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any, Mapping, Sequence

Region = tuple[float, float, float, float]
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


def _bbox_to_xywh(bbox: Any) -> list[float]:
    """统一 bbox 到归一化 [x,y,w,h]。"""
    if hasattr(bbox, "origin") and hasattr(bbox, "size"):
        x = float(getattr(bbox.origin, "x", 0.0))
        y = float(getattr(bbox.origin, "y", 0.0))
        w = float(getattr(bbox.size, "width", 0.0))
        h = float(getattr(bbox.size, "height", 0.0))
        return [x, y, w, h]

    if isinstance(bbox, Sequence) and len(bbox) == 2:
        origin, size = bbox
        if (
            isinstance(origin, Sequence)
            and len(origin) == 2
            and isinstance(size, Sequence)
            and len(size) == 2
        ):
            return [float(origin[0]), float(origin[1]), float(size[0]), float(size[1])]

    if isinstance(bbox, Sequence) and len(bbox) == 4:
        return [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]

    return [0.0, 0.0, 0.0, 0.0]


def _detect_raw_codes(
    *,
    vision_module: Any,
    image_url: Any,
    region: Region,
    allowed_symbologies: Sequence[Any],
) -> list[dict[str, Any]]:
    """在单个区域执行 Vision 检测，返回原始结果列表。"""
    request = vision_module.VNDetectBarcodesRequest.alloc().init()
    if allowed_symbologies:
        request.setSymbologies_(list(allowed_symbologies))
    request.setRegionOfInterest_(((region[0], region[1]), (region[2], region[3])))

    try:
        handler = vision_module.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
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
    """将单个区域按规格归一化（暂不做合法性校验）。"""
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
    """归一化区域列表；未提供时返回整图区域。"""
    source_regions: Sequence[Region] = regions or ((0.0, 0.0, 1.0, 1.0),)
    return [
        _normalize_single_region(region, width=width, height=height)
        for region in source_regions
    ]


def build_success_payload(
    *,
    image_path: str,
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
    image_path: str | Path,
    *,
    regions: Sequence[tuple[float, float, float, float]] | None = None,
    barcode_types: Sequence[str] | None = None,
    max_results: int | None = None,
    min_confidence: float = 0.0,
) -> dict[str, Any]:
    """读取本地图片中的条码并返回统一结构。"""
    resolved_path = Path(image_path).expanduser().resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"图片文件不存在或不是文件：{image_path}")

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
    width, height, image_url = _load_image_size_and_url(
        image_path=resolved_path,
        ns_url_cls=ns_url_cls,
        create_image_source=create_image_source,
        copy_props_at_index=copy_props_at_index,
        prop_keys=prop_keys,
    )
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
                image_url=image_url,
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
        "image_path": str(resolved_path),
        "codes": confidence_filtered_codes,
    }


def recognize_barcodes(
    image: str | Path,
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
