"""跨 skill 坐标契约：region/bbox 对外均为 top-left 归一化语义。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MAC_BARCODE = _REPO_ROOT / "mac-barcode-read"
_MAC_OCR = _REPO_ROOT / "mac-ocr-text"

if str(_MAC_BARCODE) not in sys.path:
    sys.path.insert(0, str(_MAC_BARCODE))
if str(_MAC_OCR) not in sys.path:
    sys.path.insert(0, str(_MAC_OCR))

from mac_barcode_read.core import (  # noqa: E402
    _top_left_y_to_vision_y,
    _vision_y_to_top_left_y,
    normalize_regions as barcode_normalize_regions,
)
from mac_ocr_text.core import (  # noqa: E402
    _normalize_regions as ocr_normalize_regions,
    _vision_y_to_top_left_y as ocr_vision_y_to_top_left,
)


@pytest.mark.parametrize(
    ("regions", "width", "height"),
    [
        ([(0.1, 0.2, 0.3, 0.4)], 200, 100),
        ([(10, 20, 100, 80)], 200, 100),
        (None, 640, 480),
    ],
)
def test_region_normalization_matches_across_skills(
    regions: list[tuple[float, float, float, float]] | None,
    width: int,
    height: int,
) -> None:
    barcode_out = barcode_normalize_regions(regions=regions, width=width, height=height)
    ocr_out = ocr_normalize_regions(regions=regions, width=width, height=height)
    assert barcode_out == ocr_out


def test_vision_y_conversion_formula_matches_across_skills() -> None:
    assert ocr_vision_y_to_top_left(0.5, 0.3) == pytest.approx(_vision_y_to_top_left_y(0.5, 0.3))
    assert _top_left_y_to_vision_y(0.2, 0.4) == pytest.approx(1.0 - (0.2 + 0.4))
