from path_tools.stat import stat_items


def test_stat_items(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    result = stat_items(str(tmp_path), pattern="*.txt")
    assert result["file_count"] == 1
    assert result["total_size"] == 5
    assert "earliest_mtime" in result
    assert "latest_mtime" in result


def test_stat_empty(tmp_path):
    result = stat_items(str(tmp_path))
    assert result == {"file_count": 0, "dir_count": 0, "total_size": 0}
