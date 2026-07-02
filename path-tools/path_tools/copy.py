"""Copy files matching a pattern to a target directory."""

from __future__ import annotations

import shutil
from pathlib import Path

from path_tools.core import resolve_root, walk


def copy_items(
    root: str,
    pattern: str | None,
    target: str,
    *,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
    """Copy matching files into target directory, preserving relative structure."""
    root_path = resolve_root(root)
    target_path = Path(target).expanduser().resolve()
    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for src in walk(root_path, pattern, recursive=True):
        if src.is_dir():
            continue
        rel = src.relative_to(root_path)
        dest = target_path / rel
        try:
            if dest.exists() and not overwrite:
                raise FileExistsError(f"目标已存在: {dest}")
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            succeeded.append(str(rel).replace("\\", "/"))
        except Exception as exc:
            failed.append({"path": str(rel).replace("\\", "/"), "error": str(exc)})

    return {"succeeded": succeeded, "failed": failed}
