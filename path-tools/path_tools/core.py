"""Shared infrastructure for path-tools."""

from __future__ import annotations

from pathlib import Path


class PathToolsError(ValueError):
    """Business error raised by path-tools modules."""


def resolve_root(root: str) -> Path:
    """Resolve and validate a root directory path.

    Expands user symbols (e.g. ``~``) and resolves the path to an absolute
    path before validating existence and directory type.

    Args:
        root: Root directory path string.

    Returns:
        Path: Absolute, expanded, and validated directory path.

    Raises:
        PathToolsError: If the path does not exist or is not a directory.
    """
    p = Path(root).expanduser().resolve()
    if not p.exists():
        raise PathToolsError(f"路径不存在: {root}")
    if not p.is_dir():
        raise PathToolsError(f"不是目录: {root}")
    return p
