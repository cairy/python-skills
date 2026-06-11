# /// script
# dependencies = [
#   "PyMuPDF>=1.23.0",
# ]
# requires-python = ">=3.10"
# ///

"""pdf-tools CLI 入口 — AI 标准化调用脚本。

支持子命令：
  metadata            查看 PDF 元数据
  split               按页码范围拆分
  merge               合并多个 PDF
  rotate              旋转指定页面
  extract-text        提取纯文本
  extract-text-blocks 提取结构化文本（带坐标）
  extract-images      提取嵌入图片
  render-pages        将页面渲染为图片

成功时 stdout 输出 JSON：{"success": true, "data": ...}
失败时 stderr 输出错误信息和错误 JSON。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 让脚本在作为独立入口运行时能找到同级 pdf_tools 包
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from pdf_tools.core import open_pdf, parse_page_ranges
from pdf_tools.extract import extract_images, extract_text_blocks, extract_text_plain
from pdf_tools.metadata import get_metadata
from pdf_tools.pages import merge_pdfs, rotate_pages, split_pages
from pdf_tools.render import render_pages


def _success(data: Any) -> None:
    """输出成功 JSON 到 stdout。"""
    print(json.dumps({"success": True, "data": data}, ensure_ascii=False))


def _error(e: Exception) -> None:
    """输出错误信息到 stderr。"""
    err_type = type(e).__name__
    msg = str(e)
    print(f"Error: {msg}", file=sys.stderr)
    print(
        json.dumps({"success": False, "error": msg, "error_type": err_type}, ensure_ascii=False),
        file=sys.stderr,
    )


def _add_input_arg(parser: argparse.ArgumentParser) -> None:
    """添加标准输入文件参数。"""
    parser.add_argument("input", help="输入 PDF 文件路径")


def _add_pages_arg(parser: argparse.ArgumentParser) -> None:
    """添加页码范围参数。"""
    parser.add_argument("--pages", help="页码范围，如 '1-3,5,7-10'（默认：全部页面）")


def _add_output_arg(parser: argparse.ArgumentParser, required: bool = True) -> None:
    """添加输出文件参数。"""
    parser.add_argument("--output", "-o", required=required, help="输出文件路径")


def cmd_metadata(args: argparse.Namespace) -> None:
    with open_pdf(args.input) as doc:
        meta = get_metadata(doc)
    _success(meta.__dict__)


def cmd_split(args: argparse.Namespace) -> None:
    with open_pdf(args.input) as doc:
        pages = parse_page_ranges(args.ranges, doc.page_count)
        result = split_pages(doc, pages=pages, output_path=args.output)
    _success(result)


def cmd_merge(args: argparse.Namespace) -> None:
    result = merge_pdfs(input_paths=args.inputs, output_path=args.output)
    _success(result)


def cmd_rotate(args: argparse.Namespace) -> None:
    with open_pdf(args.input) as doc:
        pages = parse_page_ranges(args.pages, doc.page_count)
        result = rotate_pages(doc, output_path=args.output, pages=pages, angle=args.angle)
    _success(result)


def cmd_extract_text(args: argparse.Namespace) -> None:
    with open_pdf(args.input) as doc:
        if args.pages:
            pages = parse_page_ranges(args.pages, doc.page_count)
            text = extract_text_plain(doc, pages=pages)
        else:
            text = extract_text_plain(doc)
    _success(text)


def cmd_extract_text_blocks(args: argparse.Namespace) -> None:
    with open_pdf(args.input) as doc:
        if args.pages:
            pages = parse_page_ranges(args.pages, doc.page_count)
            blocks = extract_text_blocks(doc, pages=pages)
        else:
            blocks = extract_text_blocks(doc)
    # TextBlock dataclass 需要转为 dict
    _success([b.__dict__ for b in blocks])


def cmd_extract_images(args: argparse.Namespace) -> None:
    if args.output_mode == "files" and not args.output_dir:
        raise ValueError("--output-dir 在 --output-mode files 时为必填参数")
    with open_pdf(args.input) as doc:
        if args.pages:
            pages = parse_page_ranges(args.pages, doc.page_count)
            images = extract_images(
                doc,
                pages=pages,
                output_mode=args.output_mode,
                output_dir=args.output_dir,
            )
        else:
            images = extract_images(
                doc,
                output_mode=args.output_mode,
                output_dir=args.output_dir,
            )
    _success([img.__dict__ for img in images])


def cmd_render_pages(args: argparse.Namespace) -> None:
    with open_pdf(args.input) as doc:
        if args.pages:
            pages = parse_page_ranges(args.pages, doc.page_count)
        else:
            pages = None
        rendered = render_pages(
            doc,
            pages=pages,
            output_dir=args.output_dir,
            dpi=args.dpi,
            fmt=args.format,
        )
    _success([p.__dict__ for p in rendered])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PDF 处理工具 — 元数据查看、页面操作、内容提取",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # metadata
    p_meta = subparsers.add_parser("metadata", help="查看 PDF 元数据")
    _add_input_arg(p_meta)

    # split
    p_split = subparsers.add_parser("split", help="按页码范围拆分 PDF")
    _add_input_arg(p_split)
    p_split.add_argument("--ranges", "-r", required=True, help="页码范围，如 '1-3,5'")
    _add_output_arg(p_split)

    # merge
    p_merge = subparsers.add_parser("merge", help="合并多个 PDF")
    p_merge.add_argument("inputs", nargs="+", help="输入 PDF 文件路径列表")
    _add_output_arg(p_merge)

    # rotate
    p_rotate = subparsers.add_parser("rotate", help="旋转指定页面")
    _add_input_arg(p_rotate)
    p_rotate.add_argument("--pages", "-p", required=True, help="要旋转的页码范围")
    p_rotate.add_argument("--angle", "-a", type=int, required=True, choices=[0, 90, 180, 270], help="旋转角度")
    _add_output_arg(p_rotate)

    # extract-text
    p_ext_text = subparsers.add_parser("extract-text", help="提取纯文本")
    _add_input_arg(p_ext_text)
    _add_pages_arg(p_ext_text)

    # extract-text-blocks
    p_ext_blocks = subparsers.add_parser("extract-text-blocks", help="提取结构化文本（带坐标）")
    _add_input_arg(p_ext_blocks)
    _add_pages_arg(p_ext_blocks)

    # extract-images
    p_ext_img = subparsers.add_parser("extract-images", help="提取嵌入图片")
    _add_input_arg(p_ext_img)
    _add_pages_arg(p_ext_img)
    p_ext_img.add_argument("--output-mode", choices=["files", "base64"], default="files", help="输出模式 (默认: files)")
    p_ext_img.add_argument("--output-dir", "-d", help="输出目录（files 模式时必填）")

    # render-pages
    p_render = subparsers.add_parser("render-pages", help="将页面渲染为图片")
    _add_input_arg(p_render)
    _add_pages_arg(p_render)
    p_render.add_argument("--output-dir", "-d", required=True, help="输出目录")
    p_render.add_argument("--dpi", type=int, default=200, help="渲染分辨率 (默认: 200)")
    p_render.add_argument("--format", choices=["png", "jpeg"], default="png", help="输出格式 (默认: png)")

    args = parser.parse_args()

    command_map = {
        "metadata": cmd_metadata,
        "split": cmd_split,
        "merge": cmd_merge,
        "rotate": cmd_rotate,
        "extract-text": cmd_extract_text,
        "extract-text-blocks": cmd_extract_text_blocks,
        "extract-images": cmd_extract_images,
        "render-pages": cmd_render_pages,
    }

    try:
        command_map[args.command](args)
        return 0
    except Exception as e:
        _error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
