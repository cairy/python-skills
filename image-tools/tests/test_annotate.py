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
