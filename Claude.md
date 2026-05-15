---
name: python-agent-skill-standard
description: 遵循 Agent Skills 开放标准的 Python 原子技能库工程规范
version: 1.0.0
---

# Python 原子技能库 全局强制规范
本文档用于约束 Claude Code 构建、重构、整理 Python 技能库的所有行为，所有规则强制执行，禁止私自修改。

**可复制模板与长示例**（各文件填空块、示例代码）：见 [`技能库模版.md`](技能库模版.md)。

## 核心原则
1.  单一职责：一个文件夹 = 一个原子功能 = 一个标准 Agent Skill
2.  人类优先：原生 Python 库面向普通开发者设计，AI 仅做标准化调用
3.  官方兼容：100% 遵循 agentskills.io 开放标准
4.  零侵入：不改造业务代码，不新增 AI 专属封装层

## 固定目录结构（不可修改）
```
skill-name/
├── SKILL.md
├── scripts/
│   └── main.py
├── evals/
│   ├── evals.json
│   └── files/
├── skill_name/
│   ├── __init__.py
│   └── core.py
├── examples/
├── tests/
├── pyproject.toml
└── README.md
```

可选：若单个 `SKILL.md` 正文过长，可在技能根目录增加 `references/`（或同级补充目录），**仅**通过现有 7 个章节**正文内的句子**引导按需阅读其中文件；不得新增第八个顶层章节，不得改变上表既有路径名称与层级。

## 各文件强制规范
### 1. scripts/main.py
- 必须使用 PEP 723 内嵌依赖声明（格式：# /// script 开头，# /// 结尾）
- 必须使用 argparse 实现命令行参数，强制支持 --help 查看用法
- 禁止交互式输入，仅支持命令行传参，不使用 stdin 传JSON
- 业务逻辑全部下沉至 skill_name/core.py，脚本仅做参数解析、调用转发、结果输出
- **stdout / stderr**：成功时仅将表示成功的 **JSON** 写入 **stdout**；日志、人类可读错误信息，以及失败时的结构化 JSON（若有）**一律**写入 **stderr**。**失败时 stdout 不得输出 JSON**（可保持无输出），以便调用方以「stdout 是否为成功 JSON」判定结果。
- 遵循幂等设计，支持合理退出码（0=成功，1=错误）

### 2. SKILL.md
- 严格使用约定的标准模板，YAML 头部格式固定，不修改字段
- name 字段必须与技能根文件夹名（短横线命名）完全一致
- 引用脚本必须使用相对路径（如 scripts/main.py），符合 Agent Skills 规范
- 必须包含7个固定章节：技能概述、能力边界、前置依赖、可用脚本、调用工作流、评测信息、开发者使用指引，不删减、不新增
- **YAML `description`（每个技能的加载摘要）**：须符合 [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) 与 agentskills 规范中的 description 字段要求——**祈使**句式（说明「何时应使用本技能」）、面向**用户意图**而非实现细节、与「能力边界」一致（含易混淆的**不适用**场景）、总长度 **≤1024** 字符；可选按该文方法维护触发评测句并迭代。

### 3. evals/ 目录
- 必须包含 evals.json（基础评测用例）和 files/（评测样本文件）
- 初期仅维护基础用例，不创建外置 workspace、iteration 等复杂流程
- 用例需包含 prompt、expected_output，可选 files 字段

### 4. skill_name/ 源码包
- 核心业务逻辑全部放在 core.py，遵循 PEP8 规范，添加完整类型提示和文档字符串
- __init__.py 仅用于导出 core.py 中的核心函数，不写业务逻辑
- 不新增任何 AI 专属适配代码，完全以普通开发者使用体验优先

### 5. 其他工程文件
- pyproject.toml：标准 Python 包配置，支持 pip install -e . 本地安装
- README.md：面向普通开发者，重点说明安装方式、原生 Python 调用示例
- examples/：存放开发者可直接运行的使用场景示例，逐步沉淀
- tests/：存放业务代码单元测试，保障核心逻辑正确性，与 evals/ 完全隔离

## Gotchas
- **`name` 与目录名**：`SKILL.md` 中 YAML `name` 必须与技能根文件夹名（kebab-case）**逐字一致**，否则 Agent 与工具链易错配。
- **evals 与 tests**：`evals/` 验证「Agent 能否按提示调用脚本并得到预期」；`tests/` 验证 `core.py` 等业务逻辑；二者不得互相替代或混写用例职责。
- **JSON 通道**：解析结果时只应信任 **stdout** 的成功 JSON；失败信息从 **stderr** 读取（含错误 JSON 时亦在 stderr）。
- **可选参数默认值**：`argparse` 与业务默认值须与 `SKILL.md` / `--help` 描述一致，避免「文档写默认可选、脚本实际必填」类偏差。

## 严格禁止行为
1.  禁止创建 _claude_skill.py 等 AI 专属适配文件
2.  禁止强制统一自定义入口函数、强制字典入参/出参
3.  禁止为适配 AI，修改原生 Python 函数的参数、返回值、调用习惯
4.  禁止打乱固定目录层级、私自新增/删除约定的文件夹/文件
5.  禁止使用非官方自定义调用协议，仅遵循标准命令行参数调用
6.  禁止将多个无关功能合并为一个技能库，必须保持原子化

## 重构&新建工作流
1.  分析原始 Python 代码，按单一职责拆分为独立原子功能
2.  为每个原子功能创建固定目录结构，严格遵循命名规范
3.  将业务逻辑迁移至 skill_name/core.py，保持原生接口不变
4.  按规范编写 scripts/main.py 入口脚本，实现参数解析和结果转发
5.  按模板生成 SKILL.md，补充基础评测用例（evals/evals.json）
6.  生成基础单元测试、示例文件、pyproject.toml 和 README.md
7.  **交付前校验（最低门槛）**：对本 skill 下 Python 路径执行 `python -m compileall`；在技能根目录执行 `uv run scripts/main.py --help`（或项目约定的等价命令）且帮助信息正确；`evals/evals.json` 可被解析且含至少 2 条用例；若已生成 `tests/`，核心用例应能通过；全库无语法错误、符合本规范。

## 与 agentskills.io 创作指南的关系（落实一致性结论）
- **通用创作原则**（上下文花费、Gotchas、校验环、渐进披露、脚本捆绑等）：见 [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices)；本仓库通过上文 **Gotchas**、**stdout/stderr**、**交付前校验**、**references/ 折中** 等条款落实。
- **每个技能的 `description` 如何写、如何测触发**：见 [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)；落实位置为各 `skill-name/SKILL.md` 的 YAML，不由本文件顶栏 `description` 承担「技能发现」语义。
- **评测与迭代**：见 [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)；在保持 `evals/` 最小结构前提下鼓励逐步加强断言与分级。
