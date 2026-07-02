import pytest
from path_tools.core import detect_rule_type, match_path, find_matching_dirs, walk


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


def test_find_matching_dirs(tmp_path):
    (tmp_path / "2024").mkdir()
    (tmp_path / "2025").mkdir()
    (tmp_path / "archive").mkdir()
    dirs = find_matching_dirs(tmp_path, ["202[0-9]"])
    names = {d.name for d in dirs}
    assert names == {"2024", "2025"}


def test_walk_glob(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.jpg").write_text("b")
    results = sorted(str(p.relative_to(tmp_path)) for p in walk(tmp_path, "*.jpg"))
    assert results == ["b.jpg"]
