import pytest
from path_tools.rename import rename_items


def test_rename_template(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    result = rename_items(str(tmp_path), pattern="*.txt", template="{stem}_{index:02d}{suffix}")
    assert (tmp_path / "a_01.txt").exists()
    assert (tmp_path / "b_02.txt").exists()


def test_rename_per_dir(tmp_path):
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    (tmp_path / "d1" / "x.txt").write_text("x")
    (tmp_path / "d2" / "y.txt").write_text("y")
    result = rename_items(str(tmp_path), pattern="**/*.txt", per_dir=True, template="{index:03d}{suffix}")
    assert (tmp_path / "d1" / "001.txt").exists()
    assert (tmp_path / "d2" / "001.txt").exists()
