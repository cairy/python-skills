"""Tests for batch directory processing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from image_tools.core import BatchResult, Box
from image_tools.pipeline import process_directory


def test_process_directory(tmp_path):
    # Create input structure
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    sample = Path("evals/files/sample_400x300.jpg").read_bytes()
    (input_dir / "a.jpg").write_bytes(sample)

    output_dir = tmp_path / "out"

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        pipeline=["resize", "convert"],
        width=200,
        height=200,
        format="png",
    )

    assert isinstance(result, BatchResult)
    assert result.success_count == 1
    assert result.failure_count == 0
    assert (output_dir / "a.png").exists()
    assert Path(result.log_path).exists()

    with open(result.log_path, encoding="utf-8") as f:
        log = json.load(f)
    assert log["success_count"] == 1
    assert log["failure_count"] == 0
    assert len(log["results"]) == 1
    assert log["results"][0]["success"] is True


def test_process_directory_failure_continues(tmp_path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    sample = Path("evals/files/sample_400x300.jpg").read_bytes()
    (input_dir / "good.jpg").write_bytes(sample)
    (input_dir / "bad.jpg").write_bytes(b"not an image")

    output_dir = tmp_path / "out"

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        pipeline=["resize"],
        width=100,
        height=100,
    )

    assert result.success_count == 1
    assert result.failure_count == 1
    assert (output_dir / "good.jpg").exists()

    with open(result.log_path, encoding="utf-8") as f:
        log = json.load(f)
    assert log["success_count"] == 1
    assert log["failure_count"] == 1
    results = log["results"]
    assert len(results) == 2
    good_entry = [r for r in results if r["success"]][0]
    bad_entry = [r for r in results if not r["success"]][0]
    assert "bad.jpg" in bad_entry["input"]
    assert "error" in bad_entry
    assert "error_type" in bad_entry


def test_process_directory_preserves_structure(tmp_path):
    input_dir = tmp_path / "in"
    (input_dir / "subdir").mkdir(parents=True)
    sample = Path("evals/files/sample_400x300.jpg").read_bytes()
    (input_dir / "top.jpg").write_bytes(sample)
    (input_dir / "subdir" / "nested.jpg").write_bytes(sample)

    output_dir = tmp_path / "out"

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        pipeline=["convert"],
        format="png",
    )

    assert result.success_count == 2
    assert result.failure_count == 0
    assert (output_dir / "top.png").exists()
    assert (output_dir / "subdir" / "nested.png").exists()

    with open(result.log_path, encoding="utf-8") as f:
        log = json.load(f)
    assert len(log["results"]) == 2
    outputs = {r["output"] for r in log["results"]}
    assert str(output_dir / "top.png") in outputs
    assert str(output_dir / "subdir" / "nested.png") in outputs


def test_process_directory_with_boxes_and_name_map(tmp_path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    sample = Path("evals/files/sample_400x300.jpg").read_bytes()
    (input_dir / "a.jpg").write_bytes(sample)

    output_dir = tmp_path / "out"

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        pipeline=["annotate", "convert"],
        format="png",
        boxes={"a.jpg": [Box(10, 10, 50, 50, "face", "red")]},
        name_map={"a.jpg": "renamed"},
    )

    assert result.success_count == 1
    assert (output_dir / "renamed.png").exists()

    with open(result.log_path, encoding="utf-8") as f:
        log = json.load(f)
    assert log["results"][0]["output"] == str(output_dir / "renamed.png")
