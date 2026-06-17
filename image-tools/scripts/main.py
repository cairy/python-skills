# /// script
# dependencies = [
#   "Pillow>=10.0.0",
# ]
# requires-python = ">=3.10"
# ///

"""image-tools CLI 入口。

支持子命令：
  process    通过 --pipeline 组合原子操作处理图片
  normalize  快捷命令：EXIF 校正 + 缩放 + 转 JPG

成功时 stdout 输出 JSON：{"success": true, "data": ...}
失败时 stderr 输出错误信息和错误 JSON。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from image_tools.core import BatchResult, Box, ProcessResult
from image_tools.pipeline import process_directory, process_image


def _success(data: Any) -> None:
    """输出成功 JSON 到 stdout。"""
    print(json.dumps({"success": True, "data": _serialize(data)}, ensure_ascii=False))


def _error(e: Exception) -> None:
    """输出错误信息到 stderr。"""
    err_type = type(e).__name__
    msg = str(e)
    print(f"Error: {msg}", file=sys.stderr)
    print(
        json.dumps({"success": False, "error": msg, "error_type": err_type}, ensure_ascii=False),
        file=sys.stderr,
    )


def _serialize(obj: Any) -> Any:
    """将结果对象序列化为 dict。"""
    if isinstance(obj, ProcessResult):
        return {
            "input_path": obj.input_path,
            "output_path": obj.output_path,
            "width": obj.width,
            "height": obj.height,
            "format": obj.format,
            "size_bytes": obj.size_bytes,
        }
    if isinstance(obj, BatchResult):
        return {
            "success_count": obj.success_count,
            "failure_count": obj.failure_count,
            "output_dir": obj.output_dir,
            "log_path": obj.log_path,
        }
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


def _parse_box(s: str) -> Box:
    """解析命令行画框参数：name,x,y,width,height,color"""
    parts = s.split(",")
    if len(parts) != 6:
        raise ValueError(f"画框参数格式错误：{s}，应为 name,x,y,width,height,color")
    name, x, y, w, h, color = parts
    return Box(
        name=name.strip(),
        x=int(x),
        y=int(y),
        width=int(w),
        height=int(h),
        color=color.strip(),
    )


def _parse_boxes_file(path: str | None) -> dict[str, list[Box]] | None:
    """解析 JSON 画框文件。"""
    if path is None:
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    boxes: dict[str, list[Box]] = {}
    for filename, box_list in data.items():
        boxes[filename] = [Box(**b) for b in box_list]
    return boxes


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--width", type=int, help="resize 目标宽度上限")
    parser.add_argument("--height", type=int, help="resize 目标高度上限")
    parser.add_argument("--format", choices=["jpg", "jpeg", "png", "webp"], default="jpg", help="输出格式 (默认: jpg)")
    parser.add_argument("--quality", type=int, default=85, help="JPEG/WebP 质量 1-100 (默认: 85)")
    parser.add_argument("--keep-exif", action="store_true", help="保留 EXIF 元数据")


def cmd_process(args: argparse.Namespace) -> None:
    pipeline = [s.strip() for s in args.pipeline.split(",") if s.strip()]
    if not pipeline:
        raise ValueError("--pipeline 不能为空")

    if args.input_dir or args.output_dir:
        if args.input or args.output:
            raise ValueError("批量模式 (--input-dir/--output-dir) 与单文件模式 (input/output) 不能混用")
        if not args.input_dir or not args.output_dir:
            raise ValueError("批量模式需要同时指定 --input-dir 和 --output-dir")

        boxes = _parse_boxes_file(args.boxes_file)
        result = process_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            pipeline=pipeline,
            width=args.width,
            height=args.height,
            format=args.format,
            quality=args.quality,
            keep_exif=args.keep_exif,
            boxes=boxes,
            log_path=args.log_file,
        )
        _success(result)
        return

    if not args.input:
        raise ValueError("单文件模式需要 input 参数")
    if not args.output:
        raise ValueError("单文件模式需要 --output 参数")

    boxes = [_parse_box(b) for b in args.box] if args.box else None
    result = process_image(
        input_path=args.input,
        output_path=args.output,
        pipeline=pipeline,
        width=args.width,
        height=args.height,
        format=args.format,
        quality=args.quality,
        keep_exif=args.keep_exif,
        boxes=boxes,
    )
    _success(result)


def cmd_normalize(args: argparse.Namespace) -> None:
    # normalize = exif-transpose,resize,convert with format jpg
    if args.input_dir or args.output_dir:
        if args.input or args.output:
            raise ValueError("批量模式与单文件模式不能混用")
        if not args.input_dir or not args.output_dir:
            raise ValueError("批量模式需要同时指定 --input-dir 和 --output-dir")
        result = process_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            pipeline=["exif-transpose", "resize", "convert"],
            width=args.width,
            height=args.height,
            format="jpg",
            quality=args.quality,
            keep_exif=args.keep_exif,
            log_path=args.log_file,
        )
        _success(result)
        return

    if not args.input or not args.output:
        raise ValueError("normalize 单文件模式需要 input 和 --output 参数")

    result = process_image(
        input_path=args.input,
        output_path=args.output,
        pipeline=["exif-transpose", "resize", "convert"],
        width=args.width,
        height=args.height,
        format="jpg",
        quality=args.quality,
        keep_exif=args.keep_exif,
    )
    _success(result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="图片预处理工具 — EXIF 校正、缩放、格式转换、压缩、批量处理、画框标注",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # process
    p_process = subparsers.add_parser("process", help="通过 --pipeline 组合原子操作处理图片")
    p_process.add_argument("input", nargs="?", help="输入图片路径（单文件模式）")
    p_process.add_argument("--output", "-o", help="输出图片路径（单文件模式）")
    p_process.add_argument("--input-dir", help="输入目录（批量模式）")
    p_process.add_argument("--output-dir", "-d", help="输出目录（批量模式）")
    p_process.add_argument("--pipeline", required=True, help="逗号分隔的原子操作序列，如 exif-transpose,resize,convert")
    p_process.add_argument("--boxes-file", help="JSON 画框文件（批量模式：文件名 -> Box 列表）")
    p_process.add_argument("--box", action="append", help="命令行画框：name,x,y,width,height,color（可多次）")
    p_process.add_argument("--log-file", help="批量结果日志路径（默认：<output-dir>/image-tools-batch.json）")
    _add_common_args(p_process)

    # normalize
    p_normalize = subparsers.add_parser("normalize", help="快捷命令：EXIF 校正 + 缩放 + 转 JPG")
    p_normalize.add_argument("input", nargs="?", help="输入图片路径（单文件模式）")
    p_normalize.add_argument("--output", "-o", help="输出图片路径（单文件模式）")
    p_normalize.add_argument("--input-dir", help="输入目录（批量模式）")
    p_normalize.add_argument("--output-dir", "-d", help="输出目录（批量模式）")
    p_normalize.add_argument("--log-file", help="批量结果日志路径")
    _add_common_args(p_normalize)

    args = parser.parse_args()

    command_map = {
        "process": cmd_process,
        "normalize": cmd_normalize,
    }

    try:
        command_map[args.command](args)
        return 0
    except Exception as e:
        _error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
