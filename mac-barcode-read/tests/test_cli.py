"""CLI 参数解析与输出协议测试。"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

import scripts.main as cli


def test_parse_regions_supports_repeated_values() -> None:
    """_parse_regions 可解析 argparse append 产生的重复值。"""
    output = cli._parse_regions(["0.1,0.2,0.3,0.4", "10,20,100,80"])

    assert output == [(0.1, 0.2, 0.3, 0.4), (10.0, 20.0, 100.0, 80.0)]


@pytest.mark.parametrize("raw", ["1,2,3", "1,2,3,4,5"])
def test_parse_regions_rejects_invalid_part_count(raw: str) -> None:
    """_parse_regions 段数不为 4 时抛 ValueError。"""
    with pytest.raises(ValueError):
        cli._parse_regions([raw])


def test_parse_regions_rejects_non_numeric_values() -> None:
    """_parse_regions 非数值字段时抛 ValueError。"""
    with pytest.raises(ValueError):
        cli._parse_regions(["1,foo,3,4"])


def test_parse_barcode_types_normalizes_case() -> None:
    """_parse_barcode_types 返回小写去重后的集合。"""
    output = cli._parse_barcode_types(["EAN13", "qrcode", "QrCode", "  "])

    assert output == {"ean13", "qrcode"}


def test_run_success_protocol(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """run 成功时 stdout 仅 success JSON，stderr 为空，exit code 为 0。"""

    def _fake_read_barcodes_from_image(*args: object, **kwargs: object) -> dict[str, object]:
        return {
            "image_path": "/tmp/demo.png",
            "codes": [{"value": "123", "barcode_type": "qrcode"}],
        }

    monkeypatch.setattr(cli, "read_barcodes_from_image", _fake_read_barcodes_from_image)
    monkeypatch.setattr(cli, "build_success_payload", cli.build_success_payload)
    monkeypatch.setattr(sys, "argv", ["main.py", "/tmp/demo.png"])

    with pytest.raises(SystemExit) as exc:
        cli.run()

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())

    assert exc.value.code == 0
    assert payload["success"] is True
    assert captured.err == ""


def test_run_failure_protocol_for_parse_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """run 参数解析失败时走统一失败协议。"""
    monkeypatch.setattr(sys, "argv", ["main.py"])

    with pytest.raises(SystemExit) as exc:
        cli.run()

    captured = capsys.readouterr()
    stderr_lines = [line for line in captured.err.strip().splitlines() if line.strip()]
    err_payload = json.loads(stderr_lines[-1])

    assert exc.value.code == 1
    assert captured.out.strip() == ""
    assert err_payload["success"] is False
    assert "error" in err_payload
