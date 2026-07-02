from path_tools.clean import clean_dir


def test_clean_removes_children(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("b")

    result = clean_dir(str(tmp_path))

    assert tmp_path.exists() and tmp_path.is_dir()
    assert not (tmp_path / "a.txt").exists()
    assert not (tmp_path / "sub").exists()
    assert sorted(result["removed"]) == ["a.txt", "sub"]
    assert result["failed"] == []


def test_clean_dry_run(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()

    result = clean_dir(str(tmp_path), dry_run=True)

    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "sub").exists()
    assert sorted(result["removed"]) == ["a.txt", "sub"]
    assert result["failed"] == []


def test_clean_skip(tmp_path):
    (tmp_path / "keep.txt").write_text("keep")
    (tmp_path / "remove.txt").write_text("remove")

    result = clean_dir(str(tmp_path), skip=["keep.txt"])

    assert (tmp_path / "keep.txt").exists()
    assert not (tmp_path / "remove.txt").exists()
    assert result["removed"] == ["remove.txt"]
    assert result["failed"] == []
