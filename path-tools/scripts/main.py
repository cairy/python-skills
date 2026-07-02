# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///

"""AI entry point for path-tools."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow the script to find path_tools when run directly without installing the package.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from path_tools.core import PathToolsError


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
        err = {"success": False, "error": "参数错误"}
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return 1

    try:
        # dispatch handled per subcommand in later tasks
        print(json.dumps({"success": True, "data": {}}, ensure_ascii=False))
        return 0
    except PathToolsError as exc:
        err = {"success": False, "error": str(exc)}
        print(f"Error: {exc}", file=sys.stderr)
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
