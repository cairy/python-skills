"""Clean directory contents without removing the directory itself."""

from __future__ import annotations

import shutil

from path_tools.core import PathToolsError, resolve_root


def clean_dir(
    root: str,
    *,
    skip: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    """Remove all children of ``root`` while keeping ``root`` itself.

    The ``root`` path is expanded and validated using :func:`resolve_root`.
    Symlinks are unlinked directly without following their targets, which
    prevents ``shutil.rmtree`` from deleting content outside of ``root``.

    Args:
        root: Path to the directory whose children should be removed.
        skip: Optional list of child names to leave untouched.
        dry_run: If ``True``, report items that would be removed without
            actually deleting anything.

    Returns:
        dict[str, object]: A dictionary with two keys:
            - ``removed``: List of child names that were (or would be) removed.
            - ``failed``: List of dictionaries describing paths that could not
              be removed, each with ``path`` and ``error`` keys.

    Raises:
        PathToolsError: If ``root`` does not exist or is not a directory.
    """
    p = resolve_root(root)

    skip = set(skip or [])
    removed: list[str] = []
    failed: list[dict[str, str]] = []

    for item in p.iterdir():
        if item.name in skip:
            continue
        try:
            if not dry_run:
                if item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            removed.append(item.name)
        except Exception as exc:
            failed.append({"path": str(item), "error": str(exc)})

    return {"removed": removed, "failed": failed}
