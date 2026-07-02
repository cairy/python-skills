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
    """Return relative paths of matching items under root.

    Args:
        root: Root directory path to search.
        pattern: Optional glob or regex pattern. If ``None`` or empty, all
            items are returned.
        recursive: Whether to recurse into subdirectories. Defaults to ``True``.
        include_dirs: Whether to include directories in the results. Defaults
            to ``False``.
        sort_by: Sorting strategy. Currently only ``"path"`` is supported,
            which sorts results alphabetically by their relative path.

    Returns:
        list[str]: Sorted relative paths (with forward slashes) of matching
            files and/or directories.

    Raises:
        PathToolsError: If ``root`` does not exist or is not a directory.
    """
    root_path = resolve_root(root)
    items = list(walk(root_path, pattern, recursive=recursive, include_dirs=include_dirs))
    rels = [str(p.relative_to(root_path)).replace("\\", "/") for p in items]
    if sort_by == "path":
        rels.sort()
    return rels
