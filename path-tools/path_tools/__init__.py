"""path_tools: local file/directory operation utilities."""

from path_tools.core import (
    PathToolsError,
    detect_rule_type,
    find_matching_dirs,
    match_path,
    resolve_root,
    walk,
)

__all__ = [
    "PathToolsError",
    "detect_rule_type",
    "find_matching_dirs",
    "match_path",
    "resolve_root",
    "walk",
]
