from path_tools.core import PathToolsError
from path_tools.list import list_items


def test_list_files_non_recursive(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.jpg").write_text("b")
    results = list_items(str(tmp_path), pattern="*.txt", recursive=False)
    assert results == ["a.txt"]


def test_list_files_recursive(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.txt").write_text("c")
    results = list_items(str(tmp_path), pattern="**/*.txt", recursive=True)
    assert sorted(results) == ["sub/c.txt"]


def test_list_include_dirs(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("a")
    results = list_items(str(tmp_path), recursive=False, include_dirs=True)
    assert "sub" in results


def test_list_pattern_none_returns_all_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.jpg").write_text("b")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.txt").write_text("c")
    results = list_items(str(tmp_path), pattern=None)
    assert sorted(results) == ["a.txt", "b.jpg", "sub/c.txt"]


def test_list_empty_directory_returns_empty(tmp_path):
    results = list_items(str(tmp_path))
    assert results == []


def test_list_nonexistent_root_raises(tmp_path):
    missing = tmp_path / "missing"
    try:
        list_items(str(missing))
    except PathToolsError as exc:
        assert "路径不存在" in str(exc)
    else:
        raise AssertionError("Expected PathToolsError")


def test_list_sort_by_path(tmp_path):
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.txt").write_text("c")
    results = list_items(str(tmp_path), sort_by="path")
    assert results == ["a.txt", "b.txt", "sub/c.txt"]
