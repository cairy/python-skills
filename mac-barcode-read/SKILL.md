---
name: mac-barcode-read
description: >
  当需要在 macOS 上读取单张本地图片中的 1D 条码或 QR Code 并返回结构化 JSON 时使用本技能；不适用于批量处理、视频帧、PDF 文档或非 macOS 环境。
version: 0.1.0
tags: ["python", "barcode", "qrcode", "macOS"]
compatibility:
  python: ">=3.10"
---

# 技能概述
本技能提供 `mac-barcode-read` 原子能力：输入单张本地图片路径，返回统一 JSON 结构。  
当前版本聚焦命令行协议与数据契约，便于上层 Agent 稳定调用。

# 能力边界
## 可处理
- 单张本地图片路径输入。
- 条码结果标准化输出（`value`、`barcode_type`、`bbox`、`confidence`）。
- 无结果时返回空数组并保持 `success=true`。

## 不支持
- 目录批量处理、视频、PDF。
- stdin JSON 或交互式输入。
- 非 macOS 环境可用性保证。

# 前置依赖
1. Python `>=3.10`。
2. 建议使用项目虚拟环境运行（如 `.venv`）。
3. 在技能根目录执行脚本并使用 `--help` 查看参数说明。

# 可用脚本
- `scripts/main.py`：技能入口脚本，负责参数解析与 stdout/stderr JSON 通道协议。

# 调用工作流
1. 在技能根目录执行 `python scripts/main.py --help` 查看参数。
2. 使用位置参数传入图片路径，按需添加 `--region`、`--barcode-type`、`--max-results`、`--min-confidence`。
3. 仅解析 stdout 的成功 JSON；失败场景从 stderr 读取错误信息与错误 JSON。

# 评测信息
- 评测配置：`evals/evals.json`
- 评测样例目录：`evals/files/`
- 测试目录：`tests/`

# 开发者使用指引
## 本地测试
```bash
python -m compileall mac_barcode_read scripts
python scripts/main.py --help
pytest tests/test_contract.py
```

## Python 调用
```python
from mac_barcode_read import build_success_payload, read_barcodes_from_image

result = read_barcodes_from_image("example.png")
payload = build_success_payload(
    image_path=result["image_path"],
    codes=result["codes"],
)
print(payload["success"])
```
