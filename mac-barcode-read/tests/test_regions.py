"""区域归一化测试。"""

import pytest

from mac_barcode_read.core import normalize_regions


def test_normalize_regions_supports_multiple_regions() -> None:
    """支持一次传入多个区域并保持顺序。"""
    regions = [(0.1, 0.2, 0.3, 0.4), (0.2, 0.3, 0.4, 0.5)]

    output = normalize_regions(regions=regions, width=200, height=100)

    assert output == [(0.1, 0.2, 0.3, 0.4), (0.2, 0.3, 0.4, 0.5)]


def test_normalize_regions_supports_mixed_pixel_and_ratio_units() -> None:
    """x,y>=1 与 w,h>1 的像素阈值按规格换算。"""
    regions = [(10, 20, 100, 80), (0.1, 20, 0.3, 80), (10, 0.2, 100, 0.4)]

    output = normalize_regions(regions=regions, width=200, height=100)

    assert output[0] == (0.05, 0.2, 0.5, 0.8)
    assert output[1] == (0.1, 0.2, 0.3, 0.8)
    assert output[2] == (0.05, 0.2, 0.5, 0.4)


def test_normalize_regions_defaults_to_full_image_when_none() -> None:
    """regions=None 时默认返回整图区域。"""
    output = normalize_regions(regions=None, width=200, height=100)
    assert output == [(0.0, 0.0, 1.0, 1.0)]


@pytest.mark.parametrize(
    "region",
    [
        (-1, 0, 10, 10),
        (0, 0, 0, 10),
        (0, 0, 10, 0),
        (0.9, 0.2, 0.2, 0.2),
        (0.2, 0.9, 0.2, 0.2),
    ],
)
def test_normalize_regions_rejects_invalid_regions(region: tuple[float, float, float, float]) -> None:
    """非法区域需抛 ValueError（负值、零面积、越界）。"""
    with pytest.raises(ValueError):
        normalize_regions(regions=[region], width=200, height=100)
