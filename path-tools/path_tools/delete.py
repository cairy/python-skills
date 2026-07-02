"""Delete files and directories matching a pattern."""

from __future__ import annotations

import shutil
from pathlib import Path

from path_tools.core import PathToolsError, resolve_root, walk


def delete_items(
    root: str,
    pattern: str | None = None,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
    """Delete matching files and directories under root."""
    root_path = resolve_root(root)
    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for p in walk(root_path, pattern, recursive=True, include_dirs=True):
        rel = str(p.relative_to(root_path)).replace("\\", "/")
        try:
            if p.is_dir():
                if not force and any(p.iterdir()):
                    raise PathToolsError(f"目录非空，需加 --force: {rel}")
                if not dry_run:
                    shutil.rmtree(p)
            else:
                if not dry_run:
                    p.unlink()
            succeeded.append(rel)
        except Exception as exc:
            failed.append({"path": rel, "error": str(exc)})

    return {"succeeded": succeeded, "failed": failed}
