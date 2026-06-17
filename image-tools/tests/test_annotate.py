"""Tests for image_tools/annotate.py."""

from __future__ import annotations

from PIL import Image

from image_tools.annotate import draw_boxes
from image_tools.core import Box


def test_draw_boxes_returns_copy():
    img = Image.new("RGB", (100, 100), "white")
    result = draw_boxes(img, [Box(10, 10, 20, 20, "face", "red")])
    assert result is not img
    assert result.size == (100, 100)


def test_draw_boxes_default_color():
    img = Image.new("RGB", (100, 100), "white")
    result = draw_boxes(img, [Box(10, 10, 20, 20)])
    # Check that at least one pixel inside the box border changed
    assert result.getpixel((10, 10)) != (255, 255, 255)


def test_draw_boxes_uses_name_color_mapping():
    img = Image.new("RGB", (200, 200), "white")
    boxes = [
        Box(10, 10, 20, 20, name="face"),
        Box(50, 50, 20, 20, name="barcode"),
        Box(90, 90, 20, 20, name="group"),
    ]
    result = draw_boxes(img, boxes)
    assert result.getpixel((10, 10)) == (255, 0, 0)   # red
    assert result.getpixel((50, 50)) == (0, 0, 255)  # blue
    assert result.getpixel((90, 90)) == (0, 128, 0)  # green


def test_draw_boxes_explicit_color_overrides_mapping():
    img = Image.new("RGB", (100, 100), "white")
    result = draw_boxes(img, [Box(10, 10, 20, 20, name="face", color="blue")])
    assert result.getpixel((10, 10)) == (0, 0, 255)  # blue


def test_draw_boxes_unknown_name_uses_yellow():
    img = Image.new("RGB", (100, 100), "white")
    result = draw_boxes(img, [Box(10, 10, 20, 20, name="unknown")])
    assert result.getpixel((10, 10)) == (255, 255, 0)  # yellow
