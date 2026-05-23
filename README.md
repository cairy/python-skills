# Python 原子技能库

本仓库是一个遵循 [agentskills.io](https://agentskills.io) 开放标准的 Python 原子技能集合，面向普通开发者原生设计，同时兼容 AI Agent 通过标准化命令行脚本调用。

每个技能按**能力域**组织，一个能力域内可包含多个相关子功能（通过 CLI 参数或子命令暴露），包含完整的 Python 源码包、命令行入口、评测用例和开发者文档。

## 已收录技能

| 技能 | 功能 | 平台要求 |
|------|------|----------|
| [`mac-ocr-text`](mac-ocr-text/) | 基于 Apple Vision / ocrmac 执行单图 OCR，支持多区域识别 | macOS |
| [`mac-barcode-read`](mac-barcode-read/) | 基于 Apple Vision 读取单张图片中的条码/二维码 | macOS |

## 快速开始

进入任意技能目录，即可本地安装并使用：

```bash
cd mac-ocr-text
pip install -e .
uv run scripts/main.py --help
```

Python 原生调用：

```python
from mac_ocr_text.core import recognize_image_text

result = recognize_image_text("image.png")
print(result["regions"][0]["plain_text"])
```

## 仓库结构

```
python-skills/
├── mac-ocr-text/          # 原子技能：macOS OCR
├── mac-barcode-read/      # 原子技能：macOS 条码读取
├── tests/                 # 仓库级公共测试
├── docs/                  # 文档
├── 技能库模版.md           # 新建技能的标准模板
└── Claude.md              # 仓库全局构建规范
```

每个技能目录内部遵循标准结构：

```
skill-name/
├── SKILL.md               # Agent 技能描述（AI 识别核心）
├── scripts/main.py        # AI 入口脚本（PEP 723 内嵌依赖）
├── skill_name/            # Python 源码包
│   ├── __init__.py
│   ├── core.py            # 共享基础设施
│   ├── feature_a.py       # 子功能 A（可选）
│   └── feature_b.py       # 子功能 B（可选）
├── evals/                 # AI 技能评测用例
├── tests/                 # 单元测试
├── examples/              # 使用示例
├── pyproject.toml         # Python 包配置
└── README.md              # 开发者文档
```

## 规范

- **能力域原则**：一个文件夹 = 一个能力域，域内相关子功能共享依赖与基础设施
- **人类优先**：原生 Python 接口面向普通开发者，不做 AI 专属适配
- **零侵入**：不改造业务代码，不新增 AI 封装层
- **官方兼容**：100% 遵循 agentskills.io 标准

详见 [`Claude.md`](Claude.md) 与 [`技能库模版.md`](技能库模版.md)。

## 新增技能

1. 复制 `技能库模版.md` 中的目录结构与文件模板
2. 将业务逻辑下沉至 `skill_name/core.py`
3. 实现 `scripts/main.py` 命令行入口
4. 补充 `evals/evals.json` 评测用例
5. 执行交付前校验：`python -m compileall` + `uv run scripts/main.py --help`

## License

[MIT](LICENSE)
