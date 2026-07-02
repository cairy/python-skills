"""Shared infrastructure for path-tools."""

from __future__ import annotations

from pathlib import Path

import fnmatch
import os
import re
from collections.abc import Iterator


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


_GLOB_CHARS = {"*", "?", "["}
_REGEX_CHARS = {"^", "$", "(", ")", "{", "}", "|", "\\"}


def detect_rule_type(rule: str) -> str:
    """Detect whether a rule is glob, regex, prefix, or a direct name.

    The classification is used to decide how a rule should be applied to a
    relative path. Glob rules contain ``*``, ``?`` or ``[``. Regex rules contain
    common regex metacharacters. Prefix rules look like directory paths. If none
    of these indicators are present, the rule is treated as a direct directory or
    file name.

    Args:
        rule: The rule string to classify.

    Returns:
        str: One of ``"glob"``, ``"regex"``, ``"prefix"`` or ``"direct"``.
    """
    if "**" in rule or "*" in rule or "?" in rule or "[" in rule:
        return "glob"
    if any(c in rule for c in _REGEX_CHARS):
        return "regex"
    if "/" in rule or "\\" in rule:
        return "prefix"
    return "direct"


def _rule_type_for_path(rule: str) -> str:
    if any(c in rule for c in _GLOB_CHARS):
        return "glob"
    if any(c in rule for c in _REGEX_CHARS):
        return "regex"
    return "glob"


def match_path(rel_path: str, rule: str, rule_type: str) -> bool:
    """Match a relative path string against a rule.

    ``rel_path`` is normalised to forward slashes before matching. Glob rules
    without a slash only match entries directly under the root (i.e. paths
    without a separator). Regex rules are applied unchanged so that backslash
    escapes remain valid.

    Args:
        rel_path: Relative path string (using ``/`` or ``\\`` separators).
        rule: Rule pattern string.
        rule_type: Matching strategy; one of ``"glob"``, ``"regex"`` or any
            other value for prefix matching.

    Returns:
        bool: ``True`` if the path matches the rule, otherwise ``False``.
    """
    rel_path = rel_path.replace("\\", "/")
    if rule_type == "glob":
        rule = rule.replace("\\", "/")
        # A glob without a slash should not cross directory boundaries.
        if "/" in rel_path and "/" not in rule:
            return False
        return fnmatch.fnmatch(rel_path, rule)
    if rule_type == "regex":
        try:
            return bool(re.match(rule, rel_path))
        except re.error:
            return False
    rule = rule.replace("\\", "/")
    return rel_path.startswith(rule.lstrip("/"))


def find_matching_dirs(root: Path, patterns: list[str]) -> list[Path]:
    """Return directories under ``root`` matching any of the patterns.

    Patterns may be direct names, regexes, globs or directory prefixes. When
    ``patterns`` is empty, ``root`` itself is returned.

    Args:
        root: Base directory to search.
        patterns: List of patterns to match against directory names or paths.

    Returns:
        list[Path]: Sorted list of matched directories.
    """
    if not patterns:
        return [root]
    matched: set[Path] = set()
    has_recursive = any(detect_rule_type(p) in ("glob", "prefix") for p in patterns)
    candidates = root.rglob("*") if has_recursive else [d for d in root.iterdir() if d.is_dir()]
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        for pattern in patterns:
            rule_type = detect_rule_type(pattern)
            if rule_type == "direct" and candidate.parent == root and candidate.name == pattern:
                matched.add(candidate)
                break
            if rule_type == "regex" and candidate.parent == root and re.match(pattern, candidate.name):
                matched.add(candidate)
                break
            if rule_type in ("glob", "prefix") and match_path(str(candidate.relative_to(root)), pattern, rule_type):
                matched.add(candidate)
                break
    return sorted(matched)


def walk(root: Path, pattern: str | None, *, recursive: bool = True, include_dirs: bool = False) -> Iterator[Path]:
    """Yield paths under ``root`` matching ``pattern``.

    If ``pattern`` is ``None`` or empty, all paths are matched. The pattern is
    matched against the path relative to ``root``.

    Args:
        root: Base directory to walk.
        pattern: Optional glob or regex pattern. Empty or ``None`` matches all.
        recursive: Whether to recurse into subdirectories.
        include_dirs: Whether to yield directories in addition to files.

    Yields:
        Path: Matching file or directory paths under ``root``.
    """
    rule = pattern or ""
    rule_type = _rule_type_for_path(rule) if rule else "glob"

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            dirpath_path = Path(dirpath)
            if include_dirs:
                for dirname in dirnames:
                    p = dirpath_path / dirname
                    rel = str(p.relative_to(root)).replace("\\", "/")
                    if not rule or match_path(rel, rule, rule_type):
                        yield p
            for filename in filenames:
                p = dirpath_path / filename
                rel = str(p.relative_to(root)).replace("\\", "/")
                if not rule or match_path(rel, rule, rule_type):
                    yield p
    else:
        for p in root.iterdir():
            rel = str(p.relative_to(root)).replace("\\", "/")
            if not rule or match_path(rel, rule, rule_type):
                yield p
