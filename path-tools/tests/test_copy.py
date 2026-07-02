from path_tools.copy import copy_items


def test_copy_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("a")
    result = copy_items(str(tmp_path / "src"), pattern="*.txt", target=str(tmp_path / "dst"))
    assert (tmp_path / "dst" / "a.txt").exists()
    assert result["succeeded"] == ["a.txt"]


def test_copy_dry_run(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("a")
    result = copy_items(str(tmp_path / "src"), pattern="*.txt", target=str(tmp_path / "dst"), dry_run=True)
    assert not (tmp_path / "dst").exists()
    assert result["succeeded"] == ["a.txt"]
