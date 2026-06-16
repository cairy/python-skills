---
name: db-tools
description: >
  当用户需要连接关系型数据库、执行 SQL 查询或探查表结构元数据时使用本技能；
  支持 PostgreSQL、MySQL、SQL Server、Oracle、SQLite。
  不提供数据导入导出、数据库迁移、ORM 操作或连接池高级调优。
  可在 macOS 上自动处理低版本 SQL Server 的 OpenSSL TLS 1.0 兼容问题。
compatibility:
  python: ">=3.10"
metadata:
  version: "0.1.0"
  tags: ["python", "数据库", "SQL", "SQLAlchemy"]
---

# 技能概述

本 Skill 提供跨数据库的连接、查询与元数据探查能力，基于 SQLAlchemy 构建。核心能力包括：
- **连接诊断**：测试数据库是否可连通，返回驱动、服务端版本、延迟
- **SQL 执行**：执行 SELECT/INSERT/UPDATE/DELETE/DDL，支持参数化绑定
- **元数据探查**：列出表名、获取列信息
- **macOS 兼容**：连接低版本 SQL Server 时自动加载 OpenSSL TLS 1.0 配置

# 能力边界

## 可处理
- 连接 PostgreSQL、MySQL/MariaDB、SQL Server、Oracle、SQLite
- 执行 SQL 并返回 JSON 或表格文本结果
- 参数化查询（通过 `--params` 传入 JSON）
- 列出表名、查看表列信息
- macOS 下自动处理 SQL Server 低版本 OpenSSL 兼容

## 不支持
- 不提供 CSV/Excel 数据导入导出
- 不提供数据库迁移或 Schema 版本管理
- 不提供 ORM 操作封装
- 不自动发现当前目录 `.env` 文件（需显式 `--env-file`）
- CLI 默认不允许 DML/DDL（需 `--allow-write`）

# 前置依赖

1. Python >=3.10
2. SQLAlchemy >=2.0（PEP 723 内嵌依赖）
3. 对应数据库驱动按需安装：
   - PostgreSQL：`psycopg2-binary` 或 `psycopg`
   - MySQL：`mysqlclient`
   - SQL Server：`pyodbc` + 系统 ODBC 驱动
   - Oracle：`oracledb`
   - SQLite：Python 内置

# 可用脚本

- **scripts/main.py**：唯一 AI 调用入口，支持 `test`、`query`、`tables`、`columns` 子命令

# 调用工作流

## 命令行调用方式

```bash
# 测试连接
python scripts/main.py --driver sqlite --database :memory: test

# 执行查询
python scripts/main.py --driver sqlite --database :memory: \
  query "SELECT * FROM users" --limit 10

# 列出表
python scripts/main.py --driver postgresql --host localhost --database mydb \
  --username user --password pass tables

# 查看列
python scripts/main.py --driver postgresql --host localhost --database mydb \
  --username user --password pass columns users --schema public
```

## AI 调用约束

1. 仅允许调用 `scripts/main.py`，不直接访问 `db_tools/` 内部源码
2. 严格遵循 `--help` 提示的参数格式
3. 成功时仅解析 **stdout** 的 JSON；失败时从 **stderr** 读取错误
4. DML/DDL 必须传入 `--allow-write`

# 评测信息

- 评测配置文件：`evals/evals.json`

# 开发者使用指引

## 本地安装

```bash
pip install -e .
```

## Python 原生调用

```python
from db_tools import build_config, create_engine_from_config, execute_query
from sqlalchemy import text

config = build_config(driver="sqlite", database=":memory:")
engine = create_engine_from_config(config)

with engine.connect() as conn:
    conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
    conn.commit()
    result = execute_query(conn, "SELECT * FROM users")
    print(result)
```
