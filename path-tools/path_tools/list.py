"""List files and directories matching a pattern."""

from __future__ import annotations

from path_tools.core import resolve_root, walk


def list_items(
    root: str,
    pattern: str | None = None,
    *,
    recursive: bool = True,
    include_dirs: bool = False,
    sort_by: str = "path",
) -> list[str]:
    """Return relative paths of matching items under root."""
    root_path = resolve_root(root)
    items = list(walk(root_path, pattern, recursive=recursive, include_dirs=include_dirs))
    rels = [str(p.relative_to(root_path)).replace("\\", "/") for p in items]
    if sort_by == "path":
        rels.sort()
    return rels
