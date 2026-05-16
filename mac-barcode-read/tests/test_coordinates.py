"""坐标系转换测试（top-left 对外，Vision lower-left 对内）。"""

import pytest

from mac_barcode_read.core import (
    _bbox_to_xywh,
    _bbox_vision_to_top_left_xywh,
    _region_top_left_to_vision,
    _top_left_y_to_vision_y,
    _vision_y_to_top_left_y,
    normalize_regions,
)


def test_vision_y_roundtrip() -> None:
    y_top = 0.2
    h = 0.4
    y_vision = _top_left_y_to_vision_y(y_top, h)
    assert y_vision == pytest.approx(0.4)
    assert _vision_y_to_top_left_y(y_vision, h) == pytest.approx(y_top)


@pytest.mark.parametrize(
    ("y_top", "h", "expected_vision_y"),
    [
        (0.0, 1.0, 0.0),
        (0.2, 0.3, 0.5),
        (0.9, 0.1, 0.0),
    ],
)
def test_top_left_y_to_vision_y(y_top: float, h: float, expected_vision_y: float) -> None:
    assert _top_left_y_to_vision_y(y_top, h) == pytest.approx(expected_vision_y)


def test_region_top_left_to_vision_full_image() -> None:
    assert _region_top_left_to_vision((0.0, 0.0, 1.0, 1.0)) == (0.0, 0.0, 1.0, 1.0)


def test_region_top_left_to_vision_partial() -> None:
    top_left = (0.1, 0.2, 0.3, 0.4)
    vision = _region_top_left_to_vision(top_left)
    assert vision[0] == pytest.approx(0.1)
    assert vision[2:] == pytest.approx((0.3, 0.4))
    assert vision[1] == pytest.approx(_top_left_y_to_vision_y(0.2, 0.4))


def test_bbox_vision_to_top_left() -> None:
    assert _bbox_vision_to_top_left_xywh(0.1, 0.5, 0.2, 0.3) == pytest.approx(
        [0.1, 0.2, 0.2, 0.3]
    )


def test_bbox_to_xywh_from_sequence() -> None:
    assert _bbox_to_xywh([0.1, 0.5, 0.2, 0.3]) == pytest.approx([0.1, 0.2, 0.2, 0.3])


def test_normalize_regions_keeps_top_left_semantics() -> None:
    """API 层 normalize_regions 不做 y 翻转。"""
    output = normalize_regions(regions=[(0.1, 0.2, 0.3, 0.4)], width=200, height=100)
    assert output == [(0.1, 0.2, 0.3, 0.4)]
