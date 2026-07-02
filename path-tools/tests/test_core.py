import pytest
from pathlib import Path

from path_tools.core import (
    PathToolsError,
    detect_rule_type,
    find_matching_dirs,
    match_path,
    resolve_root,
    walk,
)


def test_detect_rule_type_glob():
    assert detect_rule_type("*.jpg") == "glob"
    assert detect_rule_type("**/*.png") == "glob"


def test_detect_rule_type_regex():
    assert detect_rule_type(r"\d{4}") == "regex"


def test_detect_rule_type_direct():
    assert detect_rule_type("2024") == "direct"


def test_match_path_glob():
    assert match_path("a/b.jpg", "*.jpg", "glob") is False
    assert match_path("b.jpg", "*.jpg", "glob") is True


def test_match_path_regex():
    assert match_path("2024.jpg", r"\d{4}\.jpg", "regex") is True


def test_match_path_invalid_regex_returns_false():
    assert match_path("anything", r"[invalid", "regex") is False


def test_match_path_prefix():
    assert match_path("src/utils/helpers.py", "src/utils", "prefix") is True
    assert match_path("src/other.py", "src/utils", "prefix") is False


def test_resolve_root_success(tmp_path):
    resolved = resolve_root(str(tmp_path))
    assert resolved == tmp_path.resolve()


def test_resolve_root_failure(tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(PathToolsError):
        resolve_root(str(missing))

    file_path = tmp_path / "file.txt"
    file_path.write_text("not a directory")
    with pytest.raises(PathToolsError):
        resolve_root(str(file_path))


def test_find_matching_dirs(tmp_path):
    (tmp_path / "2024").mkdir()
    (tmp_path / "2025").mkdir()
    (tmp_path / "archive").mkdir()
    dirs = find_matching_dirs(tmp_path, ["202[0-9]"])
    names = {d.name for d in dirs}
    assert names == {"2024", "2025"}


def test_find_matching_dirs_prefix(tmp_path):
    (tmp_path / "src" / "utils").mkdir(parents=True)
    (tmp_path / "src" / "other").mkdir(parents=True)
    (tmp_path / "lib" / "utils").mkdir(parents=True)
    dirs = find_matching_dirs(tmp_path, ["src/utils"])
    names = {str(d.relative_to(tmp_path)) for d in dirs}
    assert names == {"src/utils"}


def test_walk_glob(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.jpg").write_text("b")
    results = sorted(str(p.relative_to(tmp_path)) for p in walk(tmp_path, "*.jpg"))
    assert results == ["b.jpg"]


def test_walk_non_recursive(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("b")
    results = sorted(str(p.relative_to(tmp_path)) for p in walk(tmp_path, "*.txt", recursive=False))
    assert results == ["a.txt"]


def test_walk_include_dirs(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "a.txt").write_text("a")
    results = sorted(str(p.relative_to(tmp_path)) for p in walk(tmp_path, None, include_dirs=True))
    assert "sub" in results
    assert "sub/a.txt" in results
