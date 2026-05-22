"""_load_image 输入适配测试。"""

from __future__ import annotations

from pathlib import Path
from io import BytesIO

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_SKILL_ROOT))

from mac_barcode_read.core import _load_image
from PIL import Image


def _make_rgb_pil() -> Image.Image:
    return Image.new("RGB", (100, 80), color=(255, 0, 0))


def test_load_image_from_str_path(tmp_path: Path) -> None:
    path = tmp_path / "test.png"
    _make_rgb_pil().save(path)
    img, resolved = _load_image(str(path))
    assert isinstance(img, Image.Image)
    assert resolved == path


def test_load_image_from_path(tmp_path: Path) -> None:
    path = tmp_path / "test.png"
    _make_rgb_pil().save(path)
    img, resolved = _load_image(path)
    assert isinstance(img, Image.Image)
    assert resolved == path


def test_load_image_from_bytes() -> None:
    buf = BytesIO()
    _make_rgb_pil().save(buf, format="PNG")
    img, resolved = _load_image(buf.getvalue())
    assert isinstance(img, Image.Image)
    assert resolved is None


def test_load_image_from_pil_image() -> None:
    source = _make_rgb_pil()
    img, resolved = _load_image(source)
    assert isinstance(img, Image.Image)
    assert resolved is None


def test_load_image_rejects_missing_path() -> None:
    with pytest.raises(FileNotFoundError):
        _load_image("/nonexistent/image.png")


def test_load_image_rejects_invalid_type() -> None:
    with pytest.raises(ValueError):
        _load_image(12345)  # type: ignore[arg-type]
