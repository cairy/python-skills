# /// script
# dependencies = [
#   "pyobjc-core",
#   "pyobjc-framework-Cocoa",
#   "pyobjc-framework-Quartz",
#   "pyobjc-framework-Vision",
# ]
# requires-python = ">=3.10"
# ///

"""mac-barcode-read CLI 入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from mac_barcode_read import build_success_payload, read_barcodes_from_image  # noqa: E402


class _CliArgumentParser(argparse.ArgumentParser):
    """将 argparse 参数错误转为可统一处理的异常。"""

    def error(self, message: str) -> None:
        raise ValueError(message)


def _parse_regions(region_values: Sequence[str] | None) -> list[tuple[float, float, float, float]] | None:
    """解析可重复 --region 参数。"""
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


def _parse_barcode_types(values: Sequence[str] | None) -> set[str] | None:
    """解析条码类型列表。"""
    if not values:
        return None

    parsed = {raw.strip().lower() for raw in values if raw.strip()}
    return parsed or None


def run() -> None:
    """执行参数解析并输出标准 JSON。"""
    parser = _CliArgumentParser(
        description="在 macOS 上读取单张图片中的 1D/QR 条码；成功时 stdout 仅输出 JSON。",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("image", help="待识别的本地图片路径")
    parser.add_argument(
        "--region",
        action="append",
        default=None,
        metavar="X,Y,W,H",
        help=(
            "可重复传入识别区域；按分量自动判别像素/比例："
            "x,y <1 为比例，>=1 为像素；w,h <=1 为比例，>1 为像素。"
        ),
    )
    parser.add_argument(
        "--barcode-type",
        action="append",
        default=None,
        metavar="TYPE",
        help=(
            "可重复传入条码类型过滤条件，例如 ean13、code128、qrcode；"
            "默认使用内置集合并在系统不支持时自动降级到可用子集，"
            "显式指定到不可用码制会报错退出。"
        ),
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        metavar="N",
        help="限制返回条码数量；不传表示不限制。",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        metavar="FLOAT",
        help="最小置信度阈值（0~1，默认 0）。",
    )

    try:
        args = parser.parse_args()
        result = read_barcodes_from_image(
            args.image,
            regions=_parse_regions(args.region),
            barcode_types=_parse_barcode_types(args.barcode_type),
            max_results=args.max_results,
            min_confidence=args.min_confidence,
        )
        payload: dict[str, Any] = build_success_payload(
            image_path=result["image_path"],
            codes=result["codes"],
        )
        print(json.dumps(payload, ensure_ascii=False))
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        err_payload: dict[str, Any] = {"success": False, "error": str(exc)}
        print(json.dumps(err_payload, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
