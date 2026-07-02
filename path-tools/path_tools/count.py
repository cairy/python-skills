"""Count files and directories matching a pattern."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from path_tools.core import detect_rule_type, match_path, resolve_root, walk


def _group_dir_for(path: Path, root: Path, group_pattern: str | None) -> str:
    """Return the grouping directory key for a path."""
    rel_parts = path.relative_to(root).parts
    if not group_pattern:
        return rel_parts[0] if rel_parts else "."
    rule_type = detect_rule_type(group_pattern)
    for i in range(len(rel_parts), 0, -1):
        candidate = "/".join(rel_parts[:i])
        if match_path(candidate, group_pattern, rule_type):
            return candidate
    return "."


def count_items(
    root: str,
    pattern: str | None = None,
    *,
    group_by_dir: str | bool | None = None,
) -> int | dict[str, int]:
    """Count matching items under root.

    Args:
        root: Root directory path.
        pattern: Optional matching pattern relative to root.
        group_by_dir: If None, return total count. If True, group by immediate
            subdirectories of root. If a string, group by matching ancestor directory.

    Returns:
        Total count as int, or dict of group -> count.
    """
    root_path = resolve_root(root)
    if group_by_dir is True:
        counter: dict[str, int] = Counter()
        for p in walk(root_path, pattern, recursive=True):
            rel = p.relative_to(root_path)
            group = rel.parts[0] if rel.parts else "."
            counter[group] += 1
        return dict(sorted(counter.items()))
    if isinstance(group_by_dir, str):
        counter = Counter()
        for p in walk(root_path, pattern, recursive=True):
            counter[_group_dir_for(p, root_path, group_by_dir)] += 1
        return dict(sorted(counter.items()))

    total = sum(1 for _ in walk(root_path, pattern, recursive=True))
    return total
