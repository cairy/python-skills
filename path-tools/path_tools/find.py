"""Find files matching additional size/mtime filters."""

from __future__ import annotations

from path_tools.core import resolve_root, walk


def _parse_size(size: str | int | None) -> int | None:
    """Parse a human-readable size string into bytes."""
    if size is None:
        return None
    if isinstance(size, int):
        return size
    s = str(size).strip().upper()
    multipliers = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}
    if s[-1] in multipliers:
        return int(float(s[:-1]) * multipliers[s[-1]])
    return int(s)


def find_items(
    root: str,
    pattern: str | None = None,
    *,
    min_size: str | int | None = None,
    max_size: str | int | None = None,
    older_than: float | None = None,
    newer_than: float | None = None,
) -> list[str]:
    """Find files matching pattern and optional size/mtime constraints.

    Args:
        root: Root directory path.
        pattern: Optional matching pattern relative to root.
        min_size: Minimum file size in bytes or human-readable string (e.g. "1K").
        max_size: Maximum file size in bytes or human-readable string.
        older_than: Maximum modification time as Unix timestamp.
        newer_than: Minimum modification time as Unix timestamp.

    Returns:
        Sorted list of relative file paths.
    """
    root_path = resolve_root(root)
    min_b = _parse_size(min_size)
    max_b = _parse_size(max_size)
    results: list[str] = []

    for p in walk(root_path, pattern, recursive=True):
        if p.is_dir():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        if min_b is not None and st.st_size < min_b:
            continue
        if max_b is not None and st.st_size > max_b:
            continue
        if older_than is not None and st.st_mtime > older_than:
            continue
        if newer_than is not None and st.st_mtime < newer_than:
            continue
        results.append(str(p.relative_to(root_path)).replace("\\", "/"))

    results.sort()
    return results
