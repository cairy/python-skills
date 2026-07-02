"""Compute aggregate statistics for matching paths."""

from __future__ import annotations

from path_tools.core import resolve_root, walk


def stat_items(root: str, pattern: str | None = None) -> dict[str, object]:
    """Return aggregate stats for files matching pattern under root.

    Args:
        root: Root directory path.
        pattern: Optional matching pattern relative to root.

    Returns:
        Dict with file_count, dir_count, total_size, earliest_mtime, latest_mtime.
    """
    root_path = resolve_root(root)
    file_count = 0
    dir_count = 0
    total_size = 0
    mtimes: list[float] = []

    for p in walk(root_path, pattern, recursive=True, include_dirs=True):
        if p.is_dir():
            dir_count += 1
            continue
        file_count += 1
        try:
            st = p.stat()
            total_size += st.st_size
            mtimes.append(st.st_mtime)
        except OSError:
            continue

    result: dict[str, object] = {
        "file_count": file_count,
        "dir_count": dir_count,
        "total_size": total_size,
    }
    if mtimes:
        result["earliest_mtime"] = min(mtimes)
        result["latest_mtime"] = max(mtimes)
    return result
