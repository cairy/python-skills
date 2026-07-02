# path-tools

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC)](https://docs.pytest.org/)

`path-tools` 是一个仅依赖 Python 标准库的文件/目录操作工具包，既可作为 **AI Skill** 通过命令行调用，也可以直接作为普通 Python 包导入使用。

## 特性

- 9 个子命令：列出、计数、统计、查找、复制、移动、重命名、清空、删除
- 统一 `--pattern` 匹配：glob、正则、前缀、直接名称
- 成功时 stdout 输出 JSON，失败时 stderr 输出错误 JSON
- 零第三方运行时依赖

## 环境要求

- Python >= 3.10

## 安装

### 作为可编辑包安装

```bash
cd path-tools
pip install -e .
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 使用 uv（推荐）

```bash
cd path-tools
uv pip install -e ".[dev]"
```

## 快速开始

### 命令行入口

```bash
# 直接运行脚本
uv run scripts/main.py --help

# 或安装后
python scripts/main.py --help
```

### 列出文件

```bash
uv run scripts/main.py list ./root --pattern "*.txt"
# {"success": true, "data": ["a.txt", "sub/b.txt"]}
```

## CLI 子命令参考

| 子命令 | 作用 | 常用选项 |
|--------|------|----------|
| `list` | 列出匹配的文件/目录 | `--pattern`, `--no-recursive`, `--include-dirs` |
| `count` | 统计匹配数量 | `--pattern`, `--group-by-dir` |
| `stat` | 输出属性汇总 | `--pattern` |
| `find` | 按大小/时间过滤 | `--pattern`, `--min-size`, `--max-size`, `--older-than`, `--newer-than` |
| `copy` | 批量复制 | `--pattern`, `--target`, `--overwrite`, `--dry-run` |
| `move` | 批量移动 | `--pattern`, `--target`, `--overwrite`, `--dry-run` |
| `rename` | 批量重命名 | `--pattern`, `--normalize`, `--prefix`, `--suffix`, `--regex-find`, `--regex-replace`, `--template`, `--per-dir`, `--dry-run` |
| `clean` | 清空目录内容 | `--skip`, `--dry-run` |
| `delete` | 删除匹配项 | `--pattern`, `--force`, `--dry-run` |

## 使用示例

```bash
# 列出文本文件（递归为默认行为）
uv run scripts/main.py list ./root --pattern "*.txt"

# 按直接子目录统计图片数量
uv run scripts/main.py count ./root --pattern "*.jpg" --group-by-dir

# 查看文本文件属性
uv run scripts/main.py stat ./root --pattern "*.txt"

# 查找大于 1K 的日志文件
uv run scripts/main.py find ./root --pattern "*.log" --min-size 1K

# 批量复制文本文件到目标目录
uv run scripts/main.py copy ./src --pattern "*.txt" --target ./dst

# 批量移动文本文件
uv run scripts/main.py move ./src --pattern "*.txt" --target ./dst

# 按目录批量重命名图片
uv run scripts/main.py rename ./root --pattern "*.jpg" --per-dir --template "{index:03d}{suffix}"

# 清空目录但保留指定文件
uv run scripts/main.py clean ./root --skip important.txt

# 强制删除临时文件
uv run scripts/main.py delete ./root --pattern "*.tmp" --force
```

## 模式匹配说明

`--pattern` 支持多种匹配方式：

- **glob**：`*.txt`（递归时自动匹配嵌套文件）、`**/*.py`
- **正则**：`/^img_\d+\.jpg$/`
- **前缀**：以 `/` 结尾的目录名，或无前缀的字符串前缀匹配
- **直接名称**：精确匹配文件或目录名

## Python API

安装为可编辑包后，可以直接导入模块：

```python
from pathlib import Path
from path_tools.list import list_items
from path_tools.count import count_items
from path_tools.find import find_items
from path_tools.copy import copy_items
from path_tools.rename import rename_items

# 列出文件
files = list_items("./root", pattern="*.txt")
print(files)  # ['a.txt', 'sub/b.txt']

# 统计数量
total = count_items("./root", pattern="*.txt")
print(total)  # 2

# 按目录分组统计
by_dir = count_items("./root", pattern="*.txt", group_by_dir=True)
print(by_dir)  # {'.': 1, 'sub': 1}

# 查找大文件
large = find_items("./root", pattern="*.log", min_size="1M")

# 复制文件
result = copy_items("./src", pattern="*.txt", target="./dst")
print(result["succeeded"])
print(result["failed"])

# 重命名
result = rename_items(
    "./root",
    pattern="*.jpg",
    per_dir=True,
    template="{index:03d}{suffix}",
)
```

## 开发

### 克隆并安装

```bash
git clone https://github.com/cairy/python-skills.git
cd python-skills/path-tools
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/ -v
```

### 仅运行指定模块测试

```bash
pytest tests/test_core.py -v
pytest tests/test_rename.py -v
```

### 语法检查

```bash
python -m compileall path_tools scripts
```

## 项目结构

```text
path-tools/
├── path_tools/          # 业务逻辑
│   ├── core.py          # 规则引擎、Walker、路径校验
│   ├── list.py
│   ├── count.py
│   ├── stat.py
│   ├── find.py
│   ├── copy.py
│   ├── move.py
│   ├── rename.py
│   ├── clean.py
│   └── delete.py
├── scripts/
│   └── main.py          # CLI 入口
├── tests/               # pytest 测试
├── evals/               # AI 评测用例与样本文件
├── SKILL.md             # Skill 元数据
├── README.md            # 本文件
└── pyproject.toml       # 包配置
```

## 输出约定

- **stdout**：仅输出成功 JSON，例如 `{"success": true, "data": ...}`
- **stderr**：错误信息或失败 JSON，例如 `{"success": false, "error": "...", "error_type": "..."}`
- 退出码：`0` 成功，`1` 错误

## 协议

MIT
