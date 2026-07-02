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
