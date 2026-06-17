"""Tests for image_tools/pipeline.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from image_tools.core import Box, ProcessResult
from image_tools.pipeline import process_image


def test_process_image_resize_only(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    output_path = tmp_path / "out.jpg"

    result = process_image(
        input_path=str(input_path),
        output_path=str(output_path),
        pipeline=["resize"],
        width=200,
        height=200,
    )

    assert isinstance(result, ProcessResult)
    assert result.output_path == str(output_path)
    # fit-without-pad: 400x300 scaled to fit 200x200 => 200x150
    assert result.width == 200
    assert result.height == 150
    assert output_path.exists()


def test_process_image_convert_png(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    output_path = tmp_path / "out.png"

    result = process_image(
        input_path=str(input_path),
        output_path=str(output_path),
        pipeline=["convert"],
        format="png",
    )

    assert result.format == "png"
    assert output_path.suffix == ".png"


def test_process_image_quality_reduces_size(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    high_path = tmp_path / "high.jpg"
    low_path = tmp_path / "low.jpg"

    process_image(
        input_path=str(input_path),
        output_path=str(high_path),
        pipeline=["compress"],
        quality=95,
    )
    process_image(
        input_path=str(input_path),
        output_path=str(low_path),
        pipeline=["compress"],
        quality=30,
    )

    assert low_path.stat().st_size < high_path.stat().st_size


def test_process_image_annotate(tmp_path):
    input_path = Path("evals/files/sample_400x300.jpg").resolve()
    output_path = tmp_path / "out.jpg"

    result = process_image(
        input_path=str(input_path),
        output_path=str(output_path),
        pipeline=["annotate"],
        boxes=[Box(10, 10, 50, 50, "face", "red")],
    )

    assert result.output_path == str(output_path)
    assert output_path.exists()
