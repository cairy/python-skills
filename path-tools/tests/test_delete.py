"""Tests for path_tools.delete."""

from path_tools.delete import delete_items


def test_delete_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "c.jpg").write_text("c")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.txt").write_text("d")

    result = delete_items(str(tmp_path), pattern="*.txt")

    assert not (tmp_path / "a.txt").exists()
    assert not (tmp_path / "b.txt").exists()
    assert not (sub / "d.txt").exists()
    assert (tmp_path / "c.jpg").exists()
    assert sorted(result["succeeded"]) == ["a.txt", "b.txt", "sub/d.txt"]
    assert result["failed"] == []


def test_delete_dry_run(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")

    result = delete_items(str(tmp_path), pattern="*.txt", dry_run=True)

    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "b.txt").exists()
    assert sorted(result["succeeded"]) == ["a.txt", "b.txt"]
    assert result["failed"] == []


def test_delete_empty_dir(tmp_path):
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    result = delete_items(str(tmp_path))

    assert not empty_dir.exists()
    assert result["succeeded"] == ["empty_dir"]
    assert result["failed"] == []


def test_delete_nonempty_dir_requires_force(tmp_path):
    target = tmp_path / "nonempty"
    target.mkdir()
    (target / "file.txt").write_text("content")

    result = delete_items(str(tmp_path), pattern="nonempty")

    assert target.exists()
    assert (target / "file.txt").exists()
    assert any(item["path"] == "nonempty" for item in result["failed"])
    assert "--force" in next(item["error"] for item in result["failed"] if item["path"] == "nonempty")
    assert result["succeeded"] == []


def test_delete_force_nonempty_dir(tmp_path):
    target = tmp_path / "nonempty"
    target.mkdir()
    (target / "file.txt").write_text("content")

    result = delete_items(str(tmp_path), pattern="nonempty", force=True)

    assert not target.exists()
    assert "nonempty" in result["succeeded"]


def test_delete_symlink_to_dir(tmp_path):
    target = tmp_path / "target_dir"
    target.mkdir()
    (target / "file.txt").write_text("content")
    symlink = tmp_path / "link_dir"
    symlink.symlink_to(target)

    result = delete_items(str(tmp_path), pattern="link_dir")

    assert not symlink.exists()
    assert symlink.is_symlink() is False
    assert target.exists()
    assert (target / "file.txt").exists()
    assert "link_dir" in result["succeeded"]
    assert result["failed"] == []
