"""Darwin 条件下的 Vision 集成测试。"""

from __future__ import annotations

from pathlib import Path
import platform
import sys

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from mac_barcode_read.core import recognize_barcodes

pytestmark = pytest.mark.skipif(platform.system() != "Darwin", reason="Darwin only")

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\x8f\xc1"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_recognize_barcodes_returns_basic_shape(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(_MINIMAL_PNG)

    try:
        result = recognize_barcodes(image=image_path)
    except ImportError as exc:
        pytest.skip(f"Vision backend unavailable: {exc}")

    assert "image_path" in result
    assert "codes" in result
    assert isinstance(result["codes"], list)
    if result["codes"]:
        first = result["codes"][0]
        assert "value" in first
        assert "barcode_type" in first
        assert "bbox" in first
        assert "confidence" in first
