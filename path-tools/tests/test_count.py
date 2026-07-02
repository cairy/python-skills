"""Tests for path_tools.count module."""

from path_tools.count import count_items


def test_count_total(tmp_path):
    """Total count returns the number of matching items."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    assert count_items(str(tmp_path), pattern="*.txt") == 2


def test_count_group_by_dir(tmp_path):
    """Group by immediate subdirectory counts files per top directory."""
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    (tmp_path / "d1" / "a.txt").write_text("a")
    (tmp_path / "d2" / "b.txt").write_text("b")
    (tmp_path / "d2" / "c.txt").write_text("c")
    result = count_items(str(tmp_path), pattern="**/*.txt", group_by_dir=True)
    assert result == {"d1": 1, "d2": 2}


def test_count_group_by_dir_root_files(tmp_path):
    """Files directly under root are grouped under '.' when group_by_dir=True."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("b")
    result = count_items(str(tmp_path), group_by_dir=True)
    assert result == {".": 1, "sub": 1}


def test_count_empty_directory(tmp_path):
    """Empty directory returns zero total and empty grouped counts."""
    assert count_items(str(tmp_path)) == 0
    assert count_items(str(tmp_path), group_by_dir=True) == {}


def test_count_group_by_pattern(tmp_path):
    """Group by matching ancestor directory groups files accordingly."""
    (tmp_path / "2024").mkdir()
    (tmp_path / "2025").mkdir()
    (tmp_path / "2024" / "a.txt").write_text("a")
    (tmp_path / "2025" / "b.txt").write_text("b")
    result = count_items(str(tmp_path), pattern="**/*.txt", group_by_dir="202[0-9]")
    assert result == {"2024": 1, "2025": 1}


def test_count_group_by_pattern_nomatch(tmp_path):
    """Pattern grouping with no matches collapses all items under '.'."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    result = count_items(str(tmp_path), pattern="*.txt", group_by_dir="nomatch")
    assert result == {".": 2}
