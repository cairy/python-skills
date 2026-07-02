---
name: path-tools
description: >
  当用户需要对本地文件/目录进行遍历、计数、属性查看、查找、复制、移动、重命名、清空或删除时使用本技能。
  支持 glob/正则/前缀等模式匹配，所有结果通过 stdout 返回 JSON；不处理远程路径、不解析文件内容、不启动 UI。
version: 0.1.0
tags: ["python", "工具", "文件系统"]
compatibility:
  python: ">=3.10"
---

# 技能概述

`path-tools` 提供一组本地路径操作子命令，覆盖常见的文件/目录查询与修改需求。
所有操作均通过 `scripts/main.py` 暴露为 argparse 子命令，成功时 stdout 输出 JSON，失败时 stderr 输出错误信息。

# 能力边界

## 可处理

- 本地文件/目录的遍历、计数、统计属性、条件查找。
- 批量复制、移动、重命名、清空、删除。
- 匹配规则支持 glob、正则、前缀、直接目录名。

## 不支持

- 不处理远程 / 网络 / 压缩包内部路径。
- 不解析文件内容（Excel、PDF、图片等）。
- 不启动 Web UI 或调用系统对话框。

# 前置依赖

- Python >= 3.10
- 使用 `uv run scripts/main.py` 执行，脚本无第三方依赖

# 可用脚本

- `scripts/main.py`：唯一 AI 调用入口，支持 `--help` 和子命令 `--help`

# 调用工作流

```bash
uv run scripts/main.py list ./root --pattern "*.txt"
uv run scripts/main.py count ./root --pattern "*.jpg" --group-by-dir
uv run scripts/main.py rename ./root --pattern "*.jpg" --per-dir --template "{index:03d}{suffix}" --dry-run
```

AI 仅解析 stdout 的成功 JSON；失败信息从 stderr 读取。

# 评测信息

- 配置文件：`evals/evals.json`
- 样本文件：`evals/files/`

# 开发者使用指引

```bash
pip install -e .
pytest tests/
```
