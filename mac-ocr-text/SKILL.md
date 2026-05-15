---
name: mac-ocr-text
description: >
  当用户需要在 macOS 上对单张本地图片进行文字识别，且希望按区域提取文本（支持路径输入、区域像素/比例混合传参）时使用本技能；不用于批量图片、PDF 版面分析、云端 OCR 或非 macOS 环境。
version: 0.1.0
tags: ["python", "OCR", "文本识别", "macOS"]
compatibility:
  python: ">=3.10"
---

# 技能概述
本技能基于 `ocrmac` 封装 macOS 系统 OCR（Vision / LiveText），用于对单张图片执行本地文字识别。  
支持 0/1/多个识别区域；当不传区域时自动识别整图，输出结构统一为 `data.regions`。

# 能力边界
## 可处理
- 单张本地图片路径调用（CLI）。
- Python 原生调用（路径 / `bytes` / `PIL.Image.Image`）。
- 区域参数按分量自动判别像素与比例：`x,y` 使用 `<1` 比例 / `>=1` 像素；`w,h` 使用 `<=1` 比例 / `>1` 像素。

## 不支持
- 批量图片、目录递归、视频帧 OCR。
- PDF 表格结构化、版式分析、文档重排。
- 非 macOS 环境下的可用性保证。

# 前置依赖
1. 推荐使用 `uv run` 执行脚本（脚本内含 PEP 723 依赖声明）。
2. Python 版本：`>=3.10`。
3. 运行环境需具备 macOS 系统 OCR 组件（Vision；若使用 LiveText 需系统支持）。

# 可用脚本
- `scripts/main.py`：唯一入口脚本，支持 `--help` 查看参数说明与默认值。

# 调用工作流
## 命令行调用方式（AI/开发者均可使用）
在技能根目录执行：

```bash
uv run scripts/main.py --help
uv run scripts/main.py "./evals/files/blank.ppm"
uv run scripts/main.py "./evals/files/blank.ppm" --region 10,20,120,80 --region 0.1,0.1,0.5,0.4
```

## AI 调用约束
1. 仅允许调用 `scripts/main.py`，不直接访问 `mac_ocr_text/` 内部实现。
2. 严格按 `--help` 参数格式传参，`--region` 每段必须是 `x,y,w,h`。
3. 成功时仅解析 stdout 的 JSON。
4. 失败时从 stderr 读取错误文本或错误 JSON 并修正参数后重试。

# 评测信息
- 评测配置：`evals/evals.json`
- 评测样本：`evals/files/`

基础用例关注：
- 输出结构正确（`data.regions` 总是存在）。
- 区域参数解析与错误通道行为正确（stdout/stderr 分离）。

# 开发者使用指引
## 本地安装
```bash
pip install -e .
```

## Python 原生调用
```python
from mac_ocr_text.core import recognize_image_text

result = recognize_image_text(
    image="example.png",
    regions=[(10, 20, 120, 80), (0.1, 0.1, 0.5, 0.4)],
    framework="vision",
)
print(result["regions"][0]["plain_text"])
```

## 参数说明（摘要）
- `framework`：`vision` 或 `livetext`。
- `recognition_level`、`confidence_threshold` 仅 `vision` 生效。
- `livetext_unit` 仅 `livetext` 生效。
- 区域判别规则详见 `README.md` 参数表与阈值表。
