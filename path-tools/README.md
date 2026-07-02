# path-tools

本地文件/目录操作原子技能，面向 AI/CLI 使用。成功时 stdout 输出 JSON，失败时 stderr 输出错误信息。

## 安装 / 使用

在 `path-tools` 根目录执行：

```bash
uv run scripts/main.py --help
```

或安装为本地可编辑包：

```bash
pip install -e .
python scripts/main.py --help
```

## 子命令概览

| 子命令 | 说明 |
|--------|------|
| `list` | 列出匹配的文件/目录 |
| `count` | 统计匹配的文件/目录数量 |
| `stat` | 统计匹配路径的属性 |
| `find` | 按大小/时间等条件查找文件 |
| `copy` | 复制匹配的文件到目标目录 |
| `move` | 移动匹配的文件到目标目录 |
| `rename` | 批量重命名匹配的文件 |
| `clean` | 清空目录内容（保留目录本身） |
| `delete` | 删除匹配的文件或目录 |

## 使用示例

```bash
# 列出文本文件
uv run scripts/main.py list ./root --pattern "*.txt"

# 按目录统计图片数量
uv run scripts/main.py count ./root --pattern "*.jpg" --group-by-dir

# 查看文本文件属性
uv run scripts/main.py stat ./root --pattern "*.txt"

# 查找大于 1K 的日志文件
uv run scripts/main.py find ./root --pattern "*.log" --min-size 1K

# 批量复制文本文件
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

- **glob**：`*.txt`、`**/*.py`
- **正则**：`/^img_\d+\.jpg$/`
- **前缀**：以 `/` 结尾的目录名，或无前缀的字符串前缀匹配
- **直接名称**：精确匹配文件或目录名

## 开发 / 测试

```bash
pip install -e .
pytest tests/
```
