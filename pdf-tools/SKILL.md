---
name: pdf-tools
description: >
  当用户需要对本地 PDF 进行元数据查看、页面拆分/合并/旋转或文本/图片提取时使用本技能；
  不提供 OCR、PDF 生成/编辑、加密解密、批量网络下载。
  支持跨平台运行（Linux/macOS/Windows）。
version: 0.1.0
tags: ["python", "工具", "PDF 处理", "文档处理"]
compatibility:
  python: ">=3.10"
---

# 技能概述

本 Skill 提供跨平台 PDF 处理能力，基于 PyMuPDF 单依赖实现。核心能力包括：
- **元数据查看**：页数、标题、作者、PDF 版本等信息
- **页面操作**：按页码拆分、多文件合并、指定页面旋转
- **内容提取**：纯文本提取、结构化文本块（带 top-left 坐标）、嵌入图片提取、页面渲染为图片

所有功能通过 `scripts/main.py` 命令行脚本暴露，AI Agent 可直接调用；同时提供原生 Python API 供开发者集成。

# 能力边界

## 可处理
- 本地 PDF 文件的元数据查看与信息提取
- PDF 页面拆分（按页码范围提取为新文件）
- 多个 PDF 文件合并为一个
- PDF 页面旋转（0/90/180/270 度）
- 纯文本提取（含多页合并）
- 结构化文本块提取（含 top-left 坐标和尺寸）
- 嵌入位图图片提取（保存为文件或 base64 编码）
- 页面渲染为图片（将 PDF 页面光栅化为 png/jpeg）
- 加密 PDF（需提供密码，CLI 暂不支持密码参数）

## 不支持
- 不提供 OCR 功能（扫描版 PDF 无文本层时返回空文本）
- 不支持 PDF 内容编辑、表单填写、数字签名
- 不支持 PDF 生成（从零创建 PDF）
- 不支持网络 URL 下载或远程文件处理
- CLI 暂不支持 `--password` 参数（加密 PDF 需通过 Python API）
- 不提取矢量图形（路径绘制的图形、SVG）

# 前置依赖

1. 推荐运行环境：Python >=3.10
2. 核心依赖：PyMuPDF>=1.23.0
3. scripts/main.py 采用 PEP 723 内嵌依赖声明，支持 `uv run` 零配置执行
4. 也可通过 `pip install PyMuPDF>=1.23.0` 手动安装依赖

# 可用脚本

- **scripts/main.py**：当前技能的唯一 AI 调用入口脚本，提供完整的命令行参数和帮助文档，支持 `--help` 查看用法

# 调用工作流

## 命令行调用方式

在 Skill 根目录执行：

```bash
# 查看帮助
python3 scripts/main.py --help

# 查看元数据
python3 scripts/main.py metadata input.pdf

# 拆分 PDF（提取第 1-3 页）
python3 scripts/main.py split input.pdf --ranges "1-3" --output out.pdf

# 合并多个 PDF
python3 scripts/main.py merge a.pdf b.pdf --output out.pdf

# 旋转页面
python3 scripts/main.py rotate input.pdf --pages "1,3" --angle 90 --output out.pdf

# 提取纯文本
python3 scripts/main.py extract-text input.pdf --pages "1-5"

# 提取结构化文本块
python3 scripts/main.py extract-text-blocks input.pdf

# 提取图片
python3 scripts/main.py extract-images input.pdf --output-mode files --output-dir ./imgs

# 渲染页面为图片
python3 scripts/main.py render-pages input.pdf --output-dir ./pages --dpi 200 --format png
```

## AI 调用约束

1. 仅允许调用 scripts/main.py，不直接访问 pdf_tools/ 内部源码包
2. 严格遵循 --help 提示的参数格式传参，不自定义非法参数
3. **成功时**仅解析 **stdout** 的 JSON；**失败时**不向 stdout 索取结果，错误说明与（若有）错误 JSON 均在 **stderr**
4. 调用失败时，依据 stderr 中的错误提示或错误 JSON 修正入参后重新调用

# 评测信息

本技能内置标准化评测用例，用于验证 AI 调用稳定性和输出质量：
- 评测配置文件：evals/evals.json
- 评测样本文件：evals/files/（动态生成测试 PDF）

# 开发者使用指引

## 本地工程安装

在 Skill 根目录执行：
```bash
pip install -e .
```

## Python 原生调用

```python
from pdf_tools import open_pdf, get_metadata, extract_text_plain

with open_pdf("document.pdf") as doc:
    meta = get_metadata(doc)
    print(f"页数: {meta.page_count}, 标题: {meta.title}")

    text = extract_text_plain(doc)
    print(text)
```
