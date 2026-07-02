import pytest

from path_tools.clean import clean_dir
from path_tools.core import PathToolsError


def test_clean_empty_directory(tmp_path):
    result = clean_dir(str(tmp_path))

    assert tmp_path.exists() and tmp_path.is_dir()
    assert result["removed"] == []
    assert result["failed"] == []


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


def test_clean_nonexistent_root(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(PathToolsError, match="路径不存在"):
        clean_dir(str(missing))


def test_clean_non_directory_root(tmp_path):
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("i am a file")

    with pytest.raises(PathToolsError, match="不是目录"):
        clean_dir(str(file_path))


def test_clean_symlink_to_directory_unlinked(tmp_path):
    # Place the symlink target outside of the directory being cleaned so that
    # following the symlink would delete external content.
    target_dir = tmp_path.parent / "external_target"
    target_dir.mkdir()
    (target_dir / "inside.txt").write_text("inside")

    root = tmp_path / "root"
    root.mkdir()
    link = root / "link"
    link.symlink_to(target_dir)

    result = clean_dir(str(root))

    assert not link.exists()
    assert target_dir.exists()
    assert (target_dir / "inside.txt").exists()
    assert result["removed"] == ["link"]
    assert result["failed"] == []
