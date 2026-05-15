"""core.py 单元测试。"""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

import mac_ocr_text.core as core


class DummyOCR:
    """用于替代 ocrmac.OCR 的测试桩。"""

    def __init__(self, image, **kwargs):
        self.image = image
        self.kwargs = kwargs

    def recognize(self):
        if self.kwargs.get("detail", True):
            return [("hello", 0.9, [0.1, 0.2, 0.3, 0.4])]
        return ["hello"]


@pytest.fixture(autouse=True)
def patch_ocr(monkeypatch):
    monkeypatch.setattr(core, "OCR", DummyOCR)


def _image_bytes(width: int = 10, height: int = 10) -> bytes:
    im = Image.new("RGB", (width, height), color="white")
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_none_regions_returns_single_full_region():
    result = core.recognize_image_text(image=_image_bytes(), regions=None)
    assert len(result["regions"]) == 1
    assert result["regions"][0]["box"] == [0.0, 0.0, 1.0, 1.0]


def test_region_mixed_units_is_supported():
    # x,y 为像素语义；w,h 为比例语义
    result = core.recognize_image_text(
        image=_image_bytes(width=100, height=200),
        regions=[(10, 20, 0.5, 0.25)],
    )
    box = result["regions"][0]["box"]
    assert box == [0.1, 0.1, 0.5, 0.25]


def test_invalid_region_raises_value_error():
    with pytest.raises(ValueError):
        core.recognize_image_text(
            image=_image_bytes(),
            regions=[(0.8, 0.3, 0.5, 0.3)],  # x + w > 1
        )


def test_livetext_rejects_vision_only_parameters():
    with pytest.raises(ValueError):
        core.recognize_image_text(
            image=_image_bytes(),
            framework="livetext",
            recognition_level="fast",
        )


def test_include_boxes_false_returns_null_bbox_and_confidence():
    result = core.recognize_image_text(image=_image_bytes(), include_boxes=False)
    seg = result["regions"][0]["segments"][0]
    assert seg["text"] == "hello"
    assert seg["bbox"] is None
    assert seg["confidence"] is None
