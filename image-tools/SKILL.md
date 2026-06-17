---
name: image-tools
description: >
  当用户需要对本地图片进行标准化预处理（方向校正、等比缩放、格式转换、JPEG 压缩、批量处理、调试画框）时使用本技能；
  不提供图片编辑、OCR、物体识别、网络下载、视频处理。
  支持 Linux/macOS/Windows。
version: 0.1.0
tags: ["python", "工具", "图片处理", "预处理"]
compatibility:
  python: ">=3.10"
---

# 技能概述

本 Skill 提供跨平台图片预处理能力，基于 Pillow 单依赖实现。核心能力包括：
- **方向校正**：自动读取 EXIF Orientation 并转正图片
- **等比缩放**：fit-without-pad 模式保持宽高比，指定目标尺寸上限
- **格式转换**：支持 JPG、PNG、WebP 输出
- **压缩**：同格式重新编码，调整 JPEG/WebP quality
- **批量处理**：递归处理目录，失败自动跳过并记录日志
- **调试标注**：在图片上绘制矩形框

所有功能通过 `scripts/main.py` 命令行脚本暴露，AI Agent 可直接调用；同时提供原生 Python API 供开发者集成。

# 能力边界

## 可处理
- 本地图片文件的方向校正（EXIF Orientation）
- 等比缩放（fit-without-pad，保持宽高比）
- 格式转换：JPG / PNG / WebP
- 同格式重新编码压缩（JPEG/WebP quality 调整）
- 原子操作通过 `--pipeline` 组合执行
- 批量目录处理（递归子目录）
- 调试标注：在图片上绘制矩形框

## 不支持
- 图片编辑（裁剪、旋转任意角度、滤镜、水印）
- OCR、物体识别、条码识别
- 网络图片下载
- 非图片文件处理
- 视频/动图逐帧处理

# 前置依赖

1. 推荐运行环境：Python >=3.10
2. 核心依赖：Pillow>=10.0.0
3. `scripts/main.py` 采用 PEP 723 内嵌依赖声明，支持 `uv run` 零配置执行
4. 也可通过 `pip install Pillow>=10.0.0` 手动安装依赖

# 可用脚本

- **scripts/main.py**：当前技能的唯一 AI 调用入口脚本，提供完整的命令行参数和帮助文档，支持 `--help` 查看用法

# 调用工作流

## 命令行调用方式

在 Skill 根目录执行：

```bash
# 查看帮助
python3 scripts/main.py --help

# normalize 快捷命令：EXIF 校正 + 缩放 + 转 JPG
python3 scripts/main.py normalize input.png --width 1024 --height 1024 --output out.jpg

# process 自定义 pipeline：仅压缩
python3 scripts/main.py process input.jpg --pipeline "compress" --quality 60 --output out.jpg

# process 批量目录
python3 scripts/main.py process \
  --input-dir ./photos \
  --output-dir ./processed \
  --pipeline "exif-transpose,resize,convert" \
  --width 1024 \
  --height 1024 \
  --format jpg

# process 画框标注
python3 scripts/main.py process input.jpg \
  --pipeline "annotate" \
  --box "face,10,20,100,80,red" \
  --output out.jpg
```

## AI 调用约束

1. 仅允许调用 `scripts/main.py`，不直接访问 `image_tools/` 内部源码包
2. 严格遵循 `--help` 提示的参数格式传参，不自定义非法参数
3. **成功时**仅解析 **stdout** 的 JSON；**失败时**不向 stdout 索取结果，错误说明与（若有）错误 JSON 均在 **stderr**
4. 调用失败时，依据 stderr 中的错误提示或错误 JSON 修正入参后重新调用

# 评测信息

本技能内置标准化评测用例，用于验证 AI 调用稳定性和输出质量：
- 评测配置文件：`evals/evals.json`
- 评测样本文件：`evals/files/`

# 开发者使用指引

## 本地工程安装

在 Skill 根目录执行：
```bash
pip install -e .
```

## Python 原生调用

```python
from image_tools import process_image

result = process_image(
    input_path="input.png",
    output_path="out.jpg",
    pipeline=["exif-transpose", "resize", "convert"],
    width=1024,
    height=1024,
    format="jpg",
    quality=85,
)
print(result.output_path, result.width, result.height, result.size_bytes)
```

### 批量处理

```python
from image_tools import process_directory

batch = process_directory(
    input_dir="./photos",
    output_dir="./processed",
    pipeline=["exif-transpose", "resize", "convert"],
    width=1024,
    height=1024,
    format="jpg",
)
print(batch.success_count, batch.failure_count, batch.log_path)
```
