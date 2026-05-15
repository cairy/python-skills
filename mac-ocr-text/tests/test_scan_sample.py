"""基于 pdf整页图片提取/config.json 的扫描样本集成测试。

用于诊断主流程「识别不到」的原因（直接对 tests/test.jpg 原图跑 OCR）：
1. 若未先缩放到配置 target_resolution，宽/高与 ROI 标定画布不一致会导致偏移
2. side 区域 (228,186,56,24) 在「原图」上可能裁到空白，而「正面」在页面其他位置
3. barcode 区域 x+w 可能超出原图宽度

主程序流程见 pdf整页图片提取：先 `resize_image` 输出精确 target 尺寸，再按 ROI 识别。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

from mac_ocr_text.core import recognize_image_text

SAMPLE_IMAGE = Path(__file__).parent / "test.jpg"

# 摘自 pdf整页图片提取/config.json
TARGET_WIDTH = 1660
TARGET_HEIGHT = 2214
REGIONS = {
    "side": (228, 186, 56, 24),
    "group": (384, 256, 911, 133),
    "barcode": (1157, 50, 520, 168),
}
GROUP_KEYWORDS = ("高校", "国家", "地方")


def _ocr_region(
    image: str | Path | Image.Image,
    region: tuple[int, int, int, int],
    *,
    framework: str = "vision",
) -> str:
    result = recognize_image_text(
        image,
        regions=[region],
        framework=framework,
        languages=["zh-Hans"],
        include_boxes=False,
    )
    return result["regions"][0]["plain_text"]


def _match_group_keyword(text: str) -> str | None:
    matches = [kw for kw in GROUP_KEYWORDS if kw in text]
    if len(matches) == 1:
        return matches[0]
    return None


def _parse_side(text: str) -> str | None:
    if "正面" in text:
        return "正面"
    if "反面" in text:
        return "反面"
    return None


@pytest.fixture
def sample_path() -> Path:
    if not SAMPLE_IMAGE.is_file():
        pytest.skip(f"样本图不存在：{SAMPLE_IMAGE}")
    return SAMPLE_IMAGE


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS OCR 仅 Darwin 可用")
class TestScanSampleRegions:
    def test_sample_image_dimensions(self, sample_path: Path) -> None:
        with Image.open(sample_path) as img:
            width, height = img.size
        assert width == 1566
        assert height == 2214
        assert width != TARGET_WIDTH, "宽与配置目标不一致，区域坐标会产生偏移"

    def test_group_region_recognizes_keyword(self, sample_path: Path) -> None:
        text = _ocr_region(sample_path, REGIONS["group"])
        assert "高校" in text
        assert _match_group_keyword(text) == "高校"

    def test_side_region_empty_with_current_config(self, sample_path: Path) -> None:
        """配置中的 side 区域当前裁到空白/无关文字，无法得到正反面。"""
        text = _ocr_region(sample_path, REGIONS["side"])
        assert text == ""
        assert _parse_side(text) is None

    def test_full_page_contains_side_label_elsewhere(self, sample_path: Path) -> None:
        """整页 OCR 能找到「正面」，说明不是引擎问题，而是区域坐标不对。"""
        result = recognize_image_text(
            sample_path,
            framework="vision",
            languages=["zh-Hans"],
            include_boxes=True,
        )
        full_text = result["regions"][0]["plain_text"]
        assert "正面" in full_text

        side_segments = [
            seg
            for seg in result["regions"][0]["segments"]
            if "正面" in seg["text"] or "反面" in seg["text"]
        ]
        assert side_segments, "整页应至少有一段含正/反面标识"
        bbox = side_segments[0]["bbox"]
        assert bbox is not None
        with Image.open(sample_path) as img:
            w, h = img.size
        actual_x = int(bbox[0] * w)
        actual_y = int(bbox[1] * h)
        cfg_x, cfg_y, _, _ = REGIONS["side"]
        assert abs(actual_y - cfg_y) > 500, (
            f"配置 side.y={cfg_y} 与实测约 y={actual_y} 相差过大"
        )

    def test_config_barcode_region_invalid_on_sample_width(self, sample_path: Path) -> None:
        """barcode 区域右边界超出图片宽度，mac_ocr_text 会拒绝该 region。"""
        with Image.open(sample_path) as img:
            width, _ = img.size
        x, _, w, _ = REGIONS["barcode"]
        assert x + w > width

        with pytest.raises(ValueError, match="x\\+w 不能大于 1"):
            _ocr_region(sample_path, REGIONS["barcode"])

    def test_barcode_readable_with_clamped_region(self, sample_path: Path) -> None:
        """将 barcode 区域左移并收窄到图片内后，OCR 与 pyzbar 均可读到条码。"""
        with Image.open(sample_path) as img:
            width, _ = img.size
        x, y, _, h = REGIONS["barcode"]
        clamped = (1100, y, width - 1100, h)
        text = _ocr_region(sample_path, clamped)
        assert "8302601897" in text.replace(" ", "")
