"""Batch rename files with normalization, prefix/suffix, regex, and templates."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from path_tools.core import PathToolsError, resolve_root, walk


def _natural_sort_key(name: str) -> list[int | str]:
    parts = re.split(r"(\d+)", name)
    return [int(p) if p.isdigit() else p.lower() for p in parts if p != ""]


def _normalize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[<>\":/\\|?*\x00-\x1f]', "_", name)
    return name


def _apply_template(template: str, name: str, index: int, parent: str, mtime: float) -> str:
    stem, suffix = name, ""
    if "." in name[1:]:
        idx = name.rfind(".")
        stem, suffix = name[:idx], name[idx:]
    context = {
        "stem": stem,
        "suffix": suffix,
        "index": index,
        "parent": parent,
        "mtime": mtime,
    }
    return template.format(**context)


def rename_items(
    root: str,
    pattern: str | None = None,
    *,
    normalize: bool = False,
    prefix: str | None = None,
    suffix: str | None = None,
    strip_prefix: str | None = None,
    strip_suffix: str | None = None,
    regex_find: str | None = None,
    regex_replace: str | None = None,
    template: str | None = None,
    per_dir: bool = False,
    sort_by: str = "natural",
    start: int = 1,
    dry_run: bool = False,
) -> dict[str, object]:
    """Rename files matching pattern under root.

    Operations are applied in fixed order:
    normalize -> prefix/suffix -> regex -> template.
    """
    root_path = resolve_root(root)
    files = [p for p in walk(root_path, pattern, recursive=True) if p.is_file()]

    if sort_by == "natural":
        files.sort(key=lambda p: (_natural_sort_key(p.name), p.name))
    elif sort_by == "lexical":
        files.sort(key=lambda p: p.name.lower())
    elif sort_by == "mtime":
        files.sort(key=lambda p: p.stat().st_mtime)

    if not any(
        [normalize, prefix, suffix, strip_prefix, strip_suffix, regex_find, template]
    ):
        raise PathToolsError(
            "至少指定一个重命名操作（如 --normalize/--prefix/--suffix/--regex-find/--template）"
        )

    compiled_regex = None
    if regex_find is not None:
        compiled_regex = re.compile(regex_find)

    groups: dict[str, list[Path]] = {}
    if per_dir:
        for p in files:
            key = str(p.parent)
            groups.setdefault(key, []).append(p)
    else:
        groups["__all__"] = files

    succeeded: list[str] = []
    failed: list[dict[str, str]] = []

    for group_files in groups.values():
        tag = uuid.uuid4().hex[:12]
        temps: list[tuple[Path, Path]] = []
        finals: list[tuple[Path, Path]] = []
        dest_paths: set[Path] = set()

        for i, src in enumerate(group_files, start=start):
            parent = src.parent
            name = src.name
            parent_rel = str(src.parent.relative_to(root_path)).replace("\\", "/") if src.parent != root_path else ""
            try:
                mtime = src.stat().st_mtime
            except OSError:
                mtime = 0.0

            if normalize:
                name = _normalize_name(name)

            if strip_prefix and name.startswith(strip_prefix):
                name = name[len(strip_prefix):]
            if strip_suffix and name.endswith(strip_suffix):
                name = name[: -len(strip_suffix)]
            if prefix:
                name = prefix + name
            if suffix:
                base, ext = name, ""
                if "." in name:
                    idx = name.rfind(".")
                    base, ext = name[:idx], name[idx:]
                name = base + suffix + ext

            if compiled_regex is not None and regex_replace is not None:
                name = compiled_regex.sub(regex_replace, name)

            if template is not None:
                name = _apply_template(template, name, i, parent_rel, mtime)

            dest = parent / name
            if src.resolve() == dest.resolve():
                continue
            if dest in dest_paths:
                failed.append({"path": str(src), "error": f"目标命名冲突: {dest}"})
                continue
            dest_paths.add(dest)
            if dest.exists():
                failed.append({"path": str(src), "error": f"目标已存在: {dest}"})
                continue
            temp = parent / f".__rename_{tag}_{i}_{name}"
            temps.append((src, temp))
            finals.append((temp, dest))

        try:
            for a, b in temps:
                if not dry_run:
                    a.rename(b)
            for a, b in finals:
                if not dry_run:
                    a.rename(b)
                succeeded.append(str(b.relative_to(root_path)).replace("\\", "/"))
        except Exception as exc:
            failed.append({"path": str(a), "error": str(exc)})

    return {"succeeded": succeeded, "failed": failed}
