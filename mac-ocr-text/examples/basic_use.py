"""mac-ocr-text 基础调用示例。"""

from mac_ocr_text.core import recognize_image_text


def main() -> None:
    result = recognize_image_text(
        image="evals/files/blank.ppm",
        regions=[(0, 0, 1, 1), (1, 1, 4, 4)],
        framework="vision",
        include_boxes=True,
    )
    for region in result["regions"]:
        print(f"region#{region['region_index']} text={region['plain_text']!r}")


if __name__ == "__main__":
    main()
