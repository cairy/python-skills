"""Tests for image_tools/core.py."""

from __future__ import annotations

import pytest
from pathlib import Path

from image_tools.core import (
    BatchResult,
    Box,
    ProcessResult,
    resolve_output_path,
    validate_input_path,
    validate_output_dir,
)


def test_box_defaults():
    box = Box(x=10, y=20, width=100, height=80)
    assert box.name == ""
    assert box.color == "red"


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


def test_validate_input_path_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_input_path(tmp_path / "missing.jpg")


def test_validate_output_dir_creates(tmp_path):
    out = tmp_path / "new_dir"
    result = validate_output_dir(out)
    assert result.exists()
    assert result.is_dir()


def test_resolve_output_path_prefers_output():
    out = resolve_output_path("in.png", "out.png", None, "jpg")
    assert out == Path("out.png")


def test_resolve_output_path_in_output_dir(tmp_path):
    out = resolve_output_path("in.png", None, tmp_path, "jpg")
    assert out == tmp_path / "in.jpg"
