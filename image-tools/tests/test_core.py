"""Tests for image_tools/core.py."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch

from image_tools.core import (
    BatchResult,
    Box,
    ProcessResult,
    validate_input_path,
    validate_output_dir,
)


def test_box_defaults():
    box = Box(x=10, y=20, width=100, height=80)
    assert box.name == ""
    assert box.color == ""


def test_process_result_fields():
    result = ProcessResult(
        input_path="in.jpg",
        output_path="out.jpg",
        width=100,
        height=100,
        format="jpg",
        size_bytes=1234,
    )
    assert result.size_bytes == 1234


def test_batch_result_instantiation():
    result = BatchResult(
        success_count=5,
        failure_count=1,
        output_dir="/tmp/out",
        log_path="/tmp/out/log.json",
    )
    assert result.success_count == 5
    assert result.failure_count == 1


def test_box_negative_dimensions():
    with pytest.raises(ValueError, match="width and height must be >= 0"):
        Box(x=10, y=20, width=-1, height=80)
    with pytest.raises(ValueError, match="width and height must be >= 0"):
        Box(x=10, y=20, width=100, height=-1)


def test_validate_input_path_not_found(tmp_path):
    with pytest.raises(ValueError, match="路径不是文件"):
        validate_input_path(tmp_path)


def test_validate_output_dir_creates(tmp_path):
    out = tmp_path / "new_dir"
    result = validate_output_dir(out)
    assert result.exists()
    assert result.is_dir()


def test_validate_output_dir_exists_but_not_dir(tmp_path):
    file_path = tmp_path / "not_a_dir"
    file_path.write_text("I am a file")
    with pytest.raises(ValueError, match="输出路径已存在但不是目录"):
        validate_output_dir(file_path)


def test_validate_input_path_no_read_permission(tmp_path):
    f = tmp_path / "file.jpg"
    f.write_text("x")
    with patch("os.access", return_value=False):
        with pytest.raises(PermissionError):
            validate_input_path(f)


def test_validate_output_dir_no_write_permission(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    with patch("os.access", return_value=False):
        with pytest.raises(PermissionError):
            validate_output_dir(d)
