---
name: python-agent-skill-standard
description: 遵循 Agent Skills 开放标准的 Python 原子技能库工程规范
version: 1.0.0
---

# Python 原子技能库 全局强制规范
本文档用于约束 Claude Code 构建、重构、整理 Python 技能库的所有行为，所有规则强制执行，禁止私自修改。

**可复制模板与长示例**（各文件填空块、示例代码）：见 [`技能库模版.md`](技能库模版.md)。

## 核心原则
1.  **能力域原则**：一个文件夹 = 一个能力域 = 一个标准 Agent Skill。能力域内可包含多个相关子功能（通过 CLI 参数或子命令暴露），拆分的依据是是否有共享依赖/基础设施、触发场景是否同质
2.  人类优先：原生 Python 库面向普通开发者设计，AI 仅做标准化调用
3.  官方兼容：100% 遵循 agentskills.io 开放标准
4.  零侵入：不改造业务代码，不新增 AI 专属封装层

## 能力域拆分指导

### 合成一个 skill 的信号
- 多个功能共享同一类核心依赖（如都依赖 PyPDF）
- 多个功能共享底层基础设施（文件加载、校验、错误处理）
- 用户描述需求时不会明确区分「用 skill A 还是 skill B」，而是说「我要处理 PDF」
- 各功能的 `description` 可以用一句话自然覆盖

### 拆成多个 skill 的信号
- 功能之间无共享依赖或基础设施（如条码识别 vs OCR）
- 触发场景完全不同，一个 `description` 难以同时覆盖
- 某个功能在特定平台才有意义（如 macOS-only 的 Vision API）

### 反模式示例
- **不要**把 `pdf-split`、`pdf-merge`、`pdf-extract` 拆成三个独立 skill —— 依赖重复、代码重复、维护成本高
- **应该**合成一个 `pdf-tools` skill，内部用 `core.py` 做共享基础设施，`split.py`、`merge.py`、`extract.py` 做子功能模块

## 目录结构约束

固定不可变动的部分（文件名与相对位置）：`SKILL.md`、`scripts/main.py`、`evals/`、`pyproject.toml`、`README.md`。`

`skill_name/` 内可按功能拆分为多模块（`core.py` 做共享基础设施，`split.py` 等做子功能）。当 skill 覆盖多个子功能时，`scripts/main.py` 可通过参数 `--action` 或 `argparse` 子命令暴露多入口。

详细目录模板与填空示例见 [`技能库模版.md`](技能库模版.md)。

可选：若单个 `SKILL.md` 正文过长，可在技能根目录增加 `references/`，**仅**通过现有 7 个章节**正文内的句子**引导按需阅读其中文件；不得新增第八个顶层章节。

## 各文件红线约束

### scripts/main.py
- PEP 723 内嵌依赖声明；argparse + `--help`；禁止交互式输入
- 仅做参数解析、命令分发、结果输出，业务逻辑下沉至 `skill_name/`
- **stdout 仅输出成功 JSON**；日志、错误信息、失败 JSON **一律 stderr**
- 退出码：0=成功，1=错误

### SKILL.md
- YAML 头部字段固定；`name` 必须与目录名（kebab-case）逐字一致
- 7 个固定章节不增删：技能概述、能力边界、前置依赖、可用脚本、调用工作流、评测信息、开发者使用指引
- `description`：祈使句式、面向用户意图、含 near-miss 边界、≤1024 字符

### skill_name/
- `core.py` 存放共享基础设施；子功能可拆为独立模块
- `__init__.py` 仅导出函数，不写业务逻辑
- 所有模块遵循 PEP8、完整类型提示、Google 风格文档字符串
- **禁止**任何 AI 专属适配代码

详细模板与填空示例见 [`技能库模版.md`](技能库模版.md)。

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
6.  禁止将多个无关能力域合并为一个技能库；同一能力域内的相关子功能应合并在同一个 skill 中

## 重构&新建工作流
1.  分析原始 Python 代码，按**能力域**划分（依据：共享依赖/基础设施、触发场景同质性）
2.  为每个能力域创建目录结构，严格遵循命名规范
3.  将共享基础设施迁移至 `skill_name/core.py`，各子功能按模块拆分（如 `split.py`、`merge.py`），保持原生接口不变
4.  按规范编写 `scripts/main.py` 入口脚本，通过参数或子命令暴露多入口，实现参数解析和结果转发
5.  按模板生成 `SKILL.md`，`description` 覆盖整个能力域，补充基础评测用例（`evals/evals.json`）
6.  生成基础单元测试、示例文件、`pyproject.toml` 和 `README.md`
7.  **交付前校验（最低门槛）**：对本 skill 下 Python 路径执行 `python -m compileall`；在技能根目录执行 `uv run scripts/main.py --help`（或项目约定的等价命令）且帮助信息正确；`evals/evals.json` 可被解析且含至少 2 条用例；若已生成 `tests/`，核心用例应能通过；全库无语法错误、符合本规范。

## 与 agentskills.io 创作指南的关系（落实一致性结论）
- **通用创作原则**（上下文花费、Gotchas、校验环、渐进披露、脚本捆绑等）：见 [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices)；本仓库通过上文 **Gotchas**、**stdout/stderr**、**交付前校验**、**references/ 折中** 等条款落实。
- **每个技能的 `description` 如何写、如何测触发**：见 [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)；落实位置为各 `skill-name/SKILL.md` 的 YAML，不由本文件顶栏 `description` 承担「技能发现」语义。
- **评测与迭代**：见 [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)；在保持 `evals/` 最小结构前提下鼓励逐步加强断言与分级。
