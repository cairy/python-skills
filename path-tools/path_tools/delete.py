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
    """Delete matching files, directories, and symlinks under ``root``.

    The ``root`` path is expanded and validated using :func:`resolve_root`.
    Symlinks are unlinked directly without following their targets, matching
    the secure pattern used elsewhere so ``shutil.rmtree`` cannot delete
    content outside of ``root``.

    Args:
        root: Path to the directory tree to search.
        pattern: Optional glob pattern limiting which items are selected.
        force: If ``True``, remove non-empty directories; otherwise they are
            reported as failures.
        dry_run: If ``True``, report items that would be deleted without
            actually removing anything.

    Returns:
        dict[str, object]: A dictionary with two keys:
            - ``succeeded``: List of relative paths that were (or would be)
              deleted.
            - ``failed``: List of dictionaries describing paths that could not
              be deleted, each with ``path`` and ``error`` keys.

    Raises:
        PathToolsError: If ``root`` does not exist or is not a directory.
    """
    root_path = resolve_root(root)
    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for p in walk(root_path, pattern, recursive=True, include_dirs=True):
        rel = str(p.relative_to(root_path)).replace("\\", "/")
        try:
            if p.is_symlink():
                if not dry_run:
                    p.unlink()
            elif p.is_dir():
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
