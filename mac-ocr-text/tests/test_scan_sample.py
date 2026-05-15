"""对同目录的 test.jpg 进行 OCR 识别的简化脚本。"""

import sys
from pathlib import Path

# 将技能根目录加入 sys.path
_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from mac_ocr_text.core import recognize_image_text

SAMPLE_IMAGE = Path(__file__).parent / "test.jpg"


def test_ocr_test_jpg():
    """执行 OCR 并打印结果。"""
    if not SAMPLE_IMAGE.is_file():
        print(f"跳过：文件不存在 {SAMPLE_IMAGE}")
        return

    result = recognize_image_text(
        SAMPLE_IMAGE,
        framework="vision",
        languages=["zh-Hans"],
    )

    text = result["regions"][0]["plain_text"]
    print(f"\n{'='*20}\nOCR 结果 ({SAMPLE_IMAGE.name}):\n{text}\n{'='*20}")
    assert text != ""


if __name__ == "__main__":
    test_ocr_test_jpg()
