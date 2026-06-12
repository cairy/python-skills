# pdf-tools

当用户需要对本地 PDF 进行元数据查看、页面拆分/合并/旋转或文本/图片提取时使用本技能。
不提供 OCR、PDF 生成/编辑、加密解密、批量网络下载。支持跨平台运行（Linux/macOS/Windows）。

## 功能介绍

pdf-tools 是一个基于 PyMuPDF 的跨平台 PDF 处理原子技能，覆盖以下能力域：

- **元数据查看**：提取页数、标题、作者、创建日期、PDF 版本等核心信息
- **页面操作**：
  - 拆分：按页码范围提取为新 PDF
  - 合并：按顺序合并多个 PDF
  - 旋转：指定页面按 0/90/180/270 度旋转
- **内容提取**：
  - 纯文本提取（多页以双换行分隔）
  - 结构化文本块（带 top-left 坐标和尺寸）
  - 嵌入位图图片（保存文件或 base64 编码）
- 图片提取 fallback 渲染：当页面小元素过多时自动渲染整页
- 页面渲染为图片（将 PDF 页面光栅化为 png/jpeg）

## 安装方式

在 Skill 根目录执行：
```bash
pip install -e .
```

## 快速使用（原生 Python 调用）

```python
from pdf_tools import open_pdf, get_metadata, extract_text_plain, split_pages, extract_images, too_many_small_elements

# 查看元数据
with open_pdf("document.pdf") as doc:
    meta = get_metadata(doc)
    print(f"页数: {meta.page_count}")
    print(f"标题: {meta.title}")

# 提取文本
with open_pdf("document.pdf") as doc:
    text = extract_text_plain(doc)
    print(text)

# 拆分页面
with open_pdf("document.pdf") as doc:
    split_pages(doc, pages=[1, 3, 5], output_path="output.pdf")

# 提取图片，复杂页面自动 fallback 渲染
with open_pdf("document.pdf") as doc:
    images = extract_images(
        doc,
        output_dir="./imgs",
        fallback=too_many_small_elements(max_size_ratio=0.5, min_count=2),
        fallback_dpi=300,
    )
```

## 参数说明

### CLI 子命令

| 子命令 | 功能 | 必需参数 | 可选参数 |
|--------|------|---------|---------|
| `metadata` | 查看元数据 | `input` | — |
| `split` | 拆分 PDF | `input`, `--ranges`, `--output` | — |
| `merge` | 合并 PDF | `inputs`, `--output` | — |
| `rotate` | 旋转页面 | `input`, `--pages`, `--angle`, `--output` | — |
| `extract-text` | 提取纯文本 | `input` | `--pages` |
| `extract-text-blocks` | 提取结构化文本 | `input` | `--pages` |
| `extract-images` | 提取图片 | `input` | `--pages`, `--output-mode`, `--output-dir` |
| `render-pages` | 渲染页面为图片 | `input`, `--output-dir` | `--pages`, `--dpi`, `--format` |

## 异常说明

| 异常类型 | 触发条件 | 处理建议 |
|---------|---------|---------|
| FileNotFoundError | 输入文件不存在 | 检查文件路径是否正确 |
| PermissionError | 无读取/写入权限 | 检查文件权限 |
| ValueError | 文件损坏、密码错误、参数非法 | 检查文件有效性和参数格式 |

## 测试

1. 单元测试：在 tests/ 目录运行 pytest
2. AI 技能评测：通过 evals/evals.json 验证 AI 调用稳定性

## 坐标系说明

文本块坐标使用 top-left 像素坐标系：
- 原点在页面左上角
- x 向右增长，y 向下增长
- 坐标为绝对像素值（非归一化）

与仓库内 mac-ocr-text、mac-barcode-read 技能的坐标契约一致。

## 许可证说明

本 skill 源码以 MIT 许可证发布。但**运行时依赖** PyMuPDF（AGPL/商业双许可），
使用者若将本 skill 集成到闭源软件中分发，需自行评估 AGPL 合规性，
必要时购买 PyMuPDF 商业许可。

## License

MIT
