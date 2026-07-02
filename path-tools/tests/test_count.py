import pytest
from path_tools.count import count_items


def test_count_total(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    assert count_items(str(tmp_path), pattern="*.txt") == 2


def test_count_group_by_dir(tmp_path):
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    (tmp_path / "d1" / "a.txt").write_text("a")
    (tmp_path / "d2" / "b.txt").write_text("b")
    (tmp_path / "d2" / "c.txt").write_text("c")
    result = count_items(str(tmp_path), pattern="**/*.txt", group_by_dir=True)
    assert result == {"d1": 1, "d2": 2}


def test_count_group_by_pattern(tmp_path):
    (tmp_path / "2024").mkdir()
    (tmp_path / "2025").mkdir()
    (tmp_path / "2024" / "a.txt").write_text("a")
    (tmp_path / "2025" / "b.txt").write_text("b")
    result = count_items(str(tmp_path), pattern="**/*.txt", group_by_dir="202[0-9]")
    assert result == {"2024": 1, "2025": 1}
