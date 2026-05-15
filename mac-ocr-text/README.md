# mac-ocr-text

在 macOS 上基于 `ocrmac` 执行单图 OCR，支持多区域识别与像素/比例混合区域传参。

## 功能介绍
- 单张图片 OCR：返回结构化 `regions` 结果。
- 区域识别：支持 0/1/多个区域，不传区域时等价整图。
- 区域输入支持像素与比例按分量自动判别，输出统一为归一化坐标。

## 安装方式
```bash
pip install -e .
```

## 命令行用法
```bash
uv run scripts/main.py --help
uv run scripts/main.py "./evals/files/blank.ppm"
uv run scripts/main.py "./evals/files/blank.ppm" --region 10,20,120,80 --region 0.1,0.2,0.4,0.3
```

## Python 调用示例
```python
from mac_ocr_text.core import recognize_image_text

result = recognize_image_text(
    image="example.png",
    regions=[(10, 20, 120, 80), (0.1, 0.2, 0.4, 0.3)],
    framework="vision",
    recognition_level="accurate",
    include_boxes=True,
)
print(result["regions"][0]["plain_text"])
```

## 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image` | `str \| Path \| bytes \| PIL.Image.Image` | 必填 | 输入图像。 |
| `regions` | `Sequence[tuple[float,float,float,float]] \| None` | `None` | 识别区域；`None/[]` 表示整图。 |
| `framework` | `vision \| livetext` | `vision` | OCR 后端。 |
| `recognition_level` | `accurate \| fast` | `accurate` | 仅 `vision` 生效。 |
| `languages` | `list[str] \| None` | `None` | BCP-47 语言偏好。 |
| `confidence_threshold` | `float` | `0.0` | 仅 `vision` 生效。 |
| `include_boxes` | `bool` | `True` | 是否返回 `segments[].bbox`。 |
| `livetext_unit` | `token \| line` | `token` | 仅 `livetext` 生效。 |

## 区域阈值规则（按分量）
对每个 `--region x,y,w,h` 或 API 区域元组，分量判别规则如下：

| 分量 | 比例条件 | 像素条件 |
|------|----------|----------|
| `x` | `< 1` | `>= 1` |
| `y` | `< 1` | `>= 1` |
| `w` | `<= 1` | `> 1` |
| `h` | `<= 1` | `> 1` |

像素分量会按图像宽高换算为归一化值后再校验。

## 返回结构（简化）
```json
{
  "success": true,
  "data": {
    "resolved_path": "/abs/path/image.png",
    "framework": "vision",
    "recognition_level": "accurate",
    "include_boxes": true,
    "regions": [
      {
        "region_index": 0,
        "box": [0, 0, 1, 1],
        "plain_text": "...",
        "segments": [
          {"text": "...", "confidence": 0.98, "bbox": [0.1, 0.2, 0.3, 0.1]}
        ]
      }
    ]
  }
}
```

## 错误与退出码
- 成功：退出码 `0`，stdout 输出 `success=true` JSON。
- 失败：退出码 `1`，stderr 输出错误文本和 `success=false` JSON。

## 测试
```bash
python -m compileall mac_ocr_text scripts
uv run scripts/main.py --help
pytest
```
