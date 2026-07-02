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

from path_tools.core import PathToolsError


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


def main() -> int:
    parser = argparse.ArgumentParser(description="本地文件/目录操作工具集")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # placeholder: subcommands added in later tasks
    _ = subparsers

    try:
        args = parser.parse_args()
    except SystemExit as exc:
        code = exc.code
        if code is None or code == 0:
            return 0
        _error(ValueError("参数错误: 缺少 command 子命令"))
        return 1

    try:
        # dispatch handled per subcommand in later tasks
        _success({})
        return 0
    except PathToolsError as exc:
        _error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
