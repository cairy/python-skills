# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///

"""path-tools CLI 入口 — AI 标准化调用脚本。

支持子命令（计划）：
  list                列出目录内容
  find                按名称/Glob 查找文件
  copy                复制文件或目录
  move                移动/重命名文件或目录
  mkdir               创建目录
  exists              检查路径是否存在

成功时 stdout 输出 JSON：{"success": true, "data": ...}
失败时 stderr 输出错误信息和错误 JSON。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow the script to find path_tools when run directly without installing the package.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

import path_tools.copy as copy_mod
import path_tools.count as count_mod
import path_tools.find as find_mod
import path_tools.list as list_mod
import path_tools.stat as stat_mod


def _success(data: Any) -> None:
    """输出成功 JSON 到 stdout。"""
    print(json.dumps({"success": True, "data": data}, ensure_ascii=False))


def _error(e: Exception, *, error_type: str | None = None) -> None:
    """输出错误信息到 stderr。"""
    err_type = error_type or type(e).__name__
    msg = str(e)
    print(f"Error: {msg}", file=sys.stderr)
    print(
        json.dumps({"success": False, "error": msg, "error_type": err_type}, ensure_ascii=False),
        file=sys.stderr,
    )


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that captures the last error message."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.last_error: str | None = None

    def error(self, message: str) -> None:
        self.last_error = message
        super().error(message)


def main() -> int:
    parser = _ArgumentParser(description="本地文件/目录操作工具集")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="列出匹配的文件/目录")
    list_parser.add_argument("root", help="根目录")
    list_parser.add_argument("--pattern", default=None, help="匹配模式 (glob/正则/前缀)")
    list_parser.add_argument("--no-recursive", action="store_true", help="仅遍历直接子项")
    list_parser.add_argument("--include-dirs", action="store_true", help="包含目录")

    count_parser = subparsers.add_parser("count", help="统计匹配的文件/目录数量")
    count_parser.add_argument("root", help="根目录")
    count_parser.add_argument("--pattern", default=None, help="匹配模式")
    count_parser.add_argument(
        "--group-by-dir",
        nargs="?",
        const=True,
        default=None,
        help="按目录分组；可接目录模式，省略时按 root 直接子目录分组",
    )

    stat_parser = subparsers.add_parser("stat", help="统计匹配路径的属性")
    stat_parser.add_argument("root", help="根目录")
    stat_parser.add_argument("--pattern", default=None, help="匹配模式")

    find_parser = subparsers.add_parser("find", help="按大小/时间等条件查找文件")
    find_parser.add_argument("root", help="根目录")
    find_parser.add_argument("--pattern", default=None, help="匹配模式")
    find_parser.add_argument("--min-size", default=None, help="最小大小（字节或 1K/M/G/T）")
    find_parser.add_argument("--max-size", default=None, help="最大大小")
    find_parser.add_argument("--older-than", type=float, default=None, help="最晚修改时间（Unix 时间戳）")
    find_parser.add_argument("--newer-than", type=float, default=None, help="最早修改时间（Unix 时间戳）")

    copy_parser = subparsers.add_parser("copy", help="复制匹配的文件到目标目录")
    copy_parser.add_argument("root", help="源根目录")
    copy_parser.add_argument("--pattern", default=None, help="匹配模式")
    copy_parser.add_argument("--target", required=True, help="目标目录")
    copy_parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    copy_parser.add_argument("--dry-run", action="store_true", help="仅模拟复制")

    # placeholder: additional subcommands added in later tasks

    try:
        args = parser.parse_args()
    except SystemExit as exc:
        code = exc.code
        if code is None or code == 0:
            return 0
        msg = "参数错误"
        if parser.last_error:
            msg = f"参数错误: {parser.last_error}"
        _error(ValueError(msg), error_type="SystemExit")
        return 1

    try:
        if args.command == "list":
            result = list_mod.list_items(
                args.root,
                pattern=args.pattern,
                recursive=not args.no_recursive,
                include_dirs=args.include_dirs,
            )
            _success(result)
            return 0

        if args.command == "count":
            result = count_mod.count_items(
                args.root,
                pattern=args.pattern,
                group_by_dir=args.group_by_dir,
            )
            _success(result)
            return 0

        if args.command == "stat":
            result = stat_mod.stat_items(args.root, pattern=args.pattern)
            _success(result)
            return 0

        if args.command == "find":
            result = find_mod.find_items(
                args.root,
                pattern=args.pattern,
                min_size=args.min_size,
                max_size=args.max_size,
                older_than=args.older_than,
                newer_than=args.newer_than,
            )
            _success(result)
            return 0

        if args.command == "copy":
            result = copy_mod.copy_items(
                args.root,
                pattern=args.pattern,
                target=args.target,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
            )
            _success(result)
            return 0

        # dispatch handled per subcommand in later tasks
        _success({})
        return 0
    except Exception as exc:
        _error(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
