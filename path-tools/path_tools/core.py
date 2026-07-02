"""Shared infrastructure for path-tools."""

from __future__ import annotations

from pathlib import Path


class PathToolsError(ValueError):
    """Business error raised by path-tools modules."""


def resolve_root(root: str) -> Path:
    """Resolve and validate a root directory path."""
    p = Path(root).expanduser().resolve()
    if not p.exists():
        raise PathToolsError(f"路径不存在: {root}")
    if not p.is_dir():
        raise PathToolsError(f"不是目录: {root}")
    return p
