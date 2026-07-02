"""Clean directory contents without removing the directory itself."""

from __future__ import annotations

import shutil
from pathlib import Path

from path_tools.core import PathToolsError


def clean_dir(
    root: str,
    *,
    skip: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    """Remove all children of root directory, keeping root itself."""
    p = Path(root).expanduser().resolve()
    if not p.exists():
        raise PathToolsError(f"路径不存在: {root}")
    if not p.is_dir():
        raise PathToolsError(f"不是目录: {root}")

    skip = set(skip or [])
    removed: list[str] = []
    failed: list[dict[str, str]] = []

    for item in p.iterdir():
        if item.name in skip:
            continue
        try:
            if not dry_run:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            removed.append(item.name)
        except Exception as exc:
            failed.append({"path": str(item), "error": str(exc)})

    return {"removed": removed, "failed": failed}
