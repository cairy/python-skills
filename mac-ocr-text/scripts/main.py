# /// script
# dependencies = [
#   "ocrmac>=1.0.1",
#   "pillow>=10.0.0",
# ]
# requires-python = ">=3.10"
# ///

"""mac-ocr-text CLI 入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

# 支持在未 pip install -e . 时从技能根目录直接运行
_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from mac_ocr_text.core import recognize_image_text  # noqa: E402


def _parse_languages(s: str | None) -> list[str] | None:
    """解析语言列表参数。"""
    if not s or not s.strip():
        return None
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p] or None


def _parse_regions(region_values: Sequence[str] | None) -> list[tuple[float, float, float, float]] | None:
    """解析可重复的 --region 参数。

    Args:
        region_values: 原始命令行参数值列表，每个元素形如 `x,y,w,h`。

    Returns:
        解析后的区域列表；若未传入区域，返回 None。

    Raises:
        ValueError: 传入格式不正确或存在非数值字段。
    """
    if not region_values:
        return None

    parsed: list[tuple[float, float, float, float]] = []
    for raw in region_values:
        parts = [piece.strip() for piece in raw.split(",")]
        if len(parts) != 4:
            raise ValueError(f"--region 参数必须是 x,y,w,h 四段：{raw}")
        try:
            x, y, w, h = [float(part) for part in parts]
        except ValueError as exc:
            raise ValueError(f"--region 含非数值字段：{raw}") from exc
        parsed.append((x, y, w, h))
    return parsed


def run() -> None:
    """执行命令行解析并输出标准 JSON。"""
    parser = argparse.ArgumentParser(
        description="使用 macOS Vision/LiveText（ocrmac）从本地图片识别文字；成功时 stdout 仅输出 JSON。",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "image",
        help="待识别的本地图片文件路径",
    )
    parser.add_argument(
        "--region",
        action="append",
        default=None,
        metavar="X,Y,W,H",
        help=(
            "可重复传入识别区域；按分量自动判别像素/比例："
            "x,y <1 为比例，>=1 为像素；w,h <=1 为比例，>1 为像素"
        ),
    )
    parser.add_argument(
        "--framework",
        choices=("vision", "livetext"),
        default="vision",
        help="OCR 后端：vision（默认）或 livetext（需较新系统）",
    )
    parser.add_argument(
        "--recognition-level",
        choices=("accurate", "fast"),
        default="accurate",
        help="仅 vision 有效：accurate（默认）或 fast",
    )
    parser.add_argument(
        "--languages",
        default=None,
        metavar="LIST",
        help="语言偏好，逗号分隔 BCP-47 码，例如：zh-Hans,en",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.0,
        help="仅 vision 有效：置信度下限，默认 0",
    )
    parser.add_argument(
        "--no-boxes",
        action="store_true",
        help="不返回边界框，仅文本",
    )
    parser.add_argument(
        "--livetext-unit",
        choices=("token", "line"),
        default="token",
        help="仅 livetext 有效：token（默认）或 line",
    )

    args = parser.parse_args()

    try:
        regions = _parse_regions(args.region)
        data = recognize_image_text(
            args.image,
            regions=regions,
            framework=args.framework,
            recognition_level=args.recognition_level,
            languages=_parse_languages(args.languages),
            confidence_threshold=args.confidence_threshold,
            include_boxes=not args.no_boxes,
            livetext_unit=args.livetext_unit,
        )
        out: dict[str, Any] = {"success": True, "data": data}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        err_payload: dict[str, Any] = {"success": False, "error": str(e)}
        print(json.dumps(err_payload, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
