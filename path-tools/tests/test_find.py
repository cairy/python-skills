import os
import time
from path_tools.find import find_items, _parse_size


def test_parse_size():
    assert _parse_size("1K") == 1024
    assert _parse_size("2.5M") == int(2.5 * 1024 * 1024)
    assert _parse_size(100) == 100


def test_find_by_size(tmp_path):
    (tmp_path / "small.txt").write_text("a")
    (tmp_path / "large.txt").write_text("a" * 100)
    results = find_items(str(tmp_path), pattern="*.txt", min_size=50)
    assert results == ["large.txt"]


def test_find_by_mtime(tmp_path):
    old = tmp_path / "old.txt"
    old.write_text("old")
    # Ensure old file has a strictly older mtime across filesystems.
    past = time.time() - 1
    os.utime(old, (past, past))
    new = tmp_path / "new.txt"
    new.write_text("new")
    threshold = (old.stat().st_mtime + new.stat().st_mtime) / 2
    results = find_items(str(tmp_path), pattern="*.txt", newer_than=threshold)
    assert results == ["new.txt"]
