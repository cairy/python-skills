"""mac-barcode-read 对外返回结构与评测契约测试。"""

import json
from pathlib import Path
import sys

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from mac_barcode_read import build_success_payload


def test_build_success_payload_contract() -> None:
    image_path = "/tmp/example.png"
    codes = [
        {
            "value": "6901234567892",
            "barcode_type": "ean13",
            "bbox": [0.12, 0.64, 0.45, 0.18],
            "confidence": 0.93,
        }
    ]

    payload = build_success_payload(image_path=image_path, codes=codes)

    assert payload["success"] is True
    assert payload["data"]["image_path"] == image_path
    assert payload["data"]["codes"] == codes


def test_build_success_payload_empty_codes() -> None:
    payload = build_success_payload(image_path="/tmp/empty.png", codes=[])

    assert payload == {
        "success": True,
        "data": {"image_path": "/tmp/empty.png", "codes": []},
    }


def test_evals_json_is_parseable_and_has_minimum_cases() -> None:
    evals_path = _SKILL_ROOT / "evals" / "evals.json"
    evals_data = json.loads(evals_path.read_text(encoding="utf-8"))

    assert isinstance(evals_data, list)
    assert len(evals_data) >= 2
    for case in evals_data:
        assert isinstance(case, dict)
        assert "prompt" in case
        assert "expected_output" in case
