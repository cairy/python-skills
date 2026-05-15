"""barcode_type 过滤、类型校验与结果映射测试。"""

import pytest

from mac_barcode_read.core import (
    filter_codes_by_type,
    map_raw_code,
    normalize_and_validate_barcode_types,
)


def test_filter_codes_by_type_keeps_requested_barcode_type() -> None:
    codes = [
        {"value": "123", "barcode_type": "ean13"},
        {"value": "hello", "barcode_type": "qrcode"},
    ]

    output = filter_codes_by_type(codes, {"qrcode"})

    assert output == [{"value": "hello", "barcode_type": "qrcode"}]


def test_filter_codes_by_type_uses_barcode_type_field_name() -> None:
    codes = [
        {"value": "abc", "symbology": "qrcode"},
        {"value": "xyz", "barcode_type": "qrcode"},
    ]

    output = filter_codes_by_type(codes, {"qrcode"})

    assert output == [{"value": "xyz", "barcode_type": "qrcode"}]


def test_filter_codes_by_type_keeps_all_when_allowed_none() -> None:
    codes = [
        {"value": "123", "barcode_type": "ean13"},
        {"value": "hello", "barcode_type": "qrcode"},
    ]

    output = filter_codes_by_type(codes, None)

    assert output == codes


def test_filter_codes_by_type_keeps_all_when_allowed_empty_set() -> None:
    codes = [
        {"value": "123", "barcode_type": "ean13"},
        {"value": "hello", "barcode_type": "qrcode"},
    ]

    output = filter_codes_by_type(codes, set())

    assert output == codes


def test_normalize_and_validate_barcode_types_returns_default_when_none() -> None:
    output = normalize_and_validate_barcode_types(None)

    assert "qrcode" in output
    assert "ean13" in output


def test_normalize_and_validate_barcode_types_rejects_unknown_types() -> None:
    with pytest.raises(ValueError):
        normalize_and_validate_barcode_types(["unknown_type"])


def test_map_raw_code_returns_unified_barcode_type_fields() -> None:
    raw = {
        "payload_string_value": "hello",
        "symbology": "qrcode",
        "bbox": [0.1, 0.2, 0.3, 0.4],
        "confidence": 0.95,
    }

    output = map_raw_code(raw)

    assert output == {
        "value": "hello",
        "barcode_type": "qrcode",
        "bbox": [0.1, 0.2, 0.3, 0.4],
        "confidence": 0.95,
    }
    assert "symbology" not in output


def test_map_raw_code_uses_empty_string_when_value_missing() -> None:
    raw = {
        "value": None,
        "payload_string_value": None,
        "payloadStringValue": None,
        "barcode_type": "qrcode",
        "bbox": [0.1, 0.2, 0.3, 0.4],
    }

    output = map_raw_code(raw)

    assert output["value"] == ""
    assert output["value"] != "None"
