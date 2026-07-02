from path_tools.move import move_items


def test_move_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("a")
    result = move_items(str(tmp_path / "src"), pattern="*.txt", target=str(tmp_path / "dst"))
    assert (tmp_path / "dst" / "a.txt").exists()
    assert not (tmp_path / "src" / "a.txt").exists()
    assert result["succeeded"] == ["a.txt"]


def test_move_dry_run(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("a")
    result = move_items(str(tmp_path / "src"), pattern="*.txt", target=str(tmp_path / "dst"), dry_run=True)
    assert not (tmp_path / "dst").exists()
    assert (tmp_path / "src" / "a.txt").exists()
    assert result["succeeded"] == ["a.txt"]


def test_move_nested_structure(tmp_path):
    (tmp_path / "src" / "sub").mkdir(parents=True)
    (tmp_path / "src" / "sub" / "a.txt").write_text("a")
    result = move_items(str(tmp_path / "src"), pattern="**/*.txt", target=str(tmp_path / "dst"))
    assert (tmp_path / "dst" / "sub" / "a.txt").exists()
    assert not (tmp_path / "src" / "sub" / "a.txt").exists()
    assert result["succeeded"] == ["sub/a.txt"]


def test_move_without_overwrite_fails(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("src")
    (tmp_path / "dst").mkdir()
    (tmp_path / "dst" / "a.txt").write_text("dst")
    result = move_items(str(tmp_path / "src"), pattern="*.txt", target=str(tmp_path / "dst"))
    assert result["succeeded"] == []
    assert len(result["failed"]) == 1
    assert result["failed"][0]["path"] == "a.txt"
    assert (tmp_path / "src" / "a.txt").read_text() == "src"
    assert (tmp_path / "dst" / "a.txt").read_text() == "dst"


def test_move_overwrite_replaces(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("src")
    (tmp_path / "dst").mkdir()
    (tmp_path / "dst" / "a.txt").write_text("dst")
    result = move_items(
        str(tmp_path / "src"),
        pattern="*.txt",
        target=str(tmp_path / "dst"),
        overwrite=True,
    )
    assert result["succeeded"] == ["a.txt"]
    assert result["failed"] == []
    assert not (tmp_path / "src" / "a.txt").exists()
    assert (tmp_path / "dst" / "a.txt").read_text() == "src"


def test_move_target_inside_source_no_recursion(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.txt").write_text("a")
    result = move_items(
        str(tmp_path / "src"),
        pattern="*.txt",
        target=str(tmp_path / "src" / "backup"),
    )
    assert (tmp_path / "src" / "backup" / "a.txt").read_text() == "a"
    assert not (tmp_path / "src" / "a.txt").exists()
    assert result["succeeded"] == ["a.txt"]
    assert "backup/a.txt" not in result["succeeded"]
    assert not (tmp_path / "src" / "backup" / "backup").exists()
