"""基础使用示例：单文件 normalize 处理。"""

from pathlib import Path

from image_tools import process_image

# normalize 快捷命令等价于 pipeline=["exif-transpose", "resize", "convert"] --format jpg
result = process_image(
    input_path=Path(__file__).resolve().parents[1] / "evals" / "files" / "sample_400x300.jpg",
    output_path="output/out.jpg",
    pipeline=["exif-transpose", "resize", "convert"],
    width=1024,
    height=1024,
    format="jpg",
    quality=85,
)

print(f"输出：{result.output_path}")
print(f"尺寸：{result.width}x{result.height}")
print(f"大小：{result.size_bytes} bytes")
