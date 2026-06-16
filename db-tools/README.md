# db-tools

跨数据库连接、查询与元数据探查工具，基于 SQLAlchemy 2.x 构建。

## 功能

- **连接诊断**：测试数据库连通性，返回驱动、服务端版本与延迟。
- **SQL 执行**：执行 SELECT / INSERT / UPDATE / DELETE / DDL，支持参数化绑定。
- **元数据探查**：列出表名、查看表列信息。
- **macOS SQL Server 兼容**：在 macOS 上连接低版本 SQL Server 时，自动加载 bundled OpenSSL TLS 1.0 配置。
- **只读默认**：CLI 默认只允许 SELECT，DML/DDL 需显式传入 `--allow-write`。

## 项目结构

```
db-tools/
├── SKILL.md                      # Agent Skill 描述文件
├── README.md                     # 开发者文档
├── pyproject.toml                # 包配置
├── scripts/main.py               # CLI 入口（AI 调用唯一入口）
├── db_tools/                     # 原生 Python API
│   ├── __init__.py               # 公开 API 导出
│   ├── core.py                   # ConnectionConfig、异常体系
│   ├── config.py                 # 配置构建、.env 加载、OpenSSL workaround
│   ├── drivers.py                # 驱动枚举、ODBC 驱动发现
│   ├── engine.py                 # SQLAlchemy Engine 创建与数据库适配
│   ├── query.py                  # SQL 执行与结果序列化
│   ├── metadata.py               # 表/列元数据探查
│   └── resources/
│       └── openssl_allow_tls1.0.cnf  # macOS SQL Server OpenSSL 兼容配置
├── tests/                        # 单元测试与 CLI 测试
└── evals/
    └── evals.json                # 技能评测用例
```

## 安装

```bash
pip install -e .
```

或临时通过 `PYTHONPATH` 运行：

```bash
PYTHONPATH=. python scripts/main.py --help
```

## CLI 用法

```bash
# 测试连接
python scripts/main.py --driver sqlite --database :memory: test

# 执行查询（默认只读；:memory: 仅在单次调用内有效）
python scripts/main.py --driver sqlite --database :memory: query "SELECT 1"

# 执行写操作（:memory: 表在命令结束后即丢弃）
python scripts/main.py --driver sqlite --database :memory: \
  query "CREATE TABLE t (id INTEGER)" --allow-write

# 列出表
python scripts/main.py --driver postgresql --host localhost --database mydb \
  --username user --password pass tables

# 查看列
python scripts/main.py --driver postgresql --host localhost --database mydb \
  --username user --password pass columns users --schema public
```

> 安全提示：命令行 `--password` 会暴露在进程列表中。生产环境优先使用 `--env-file` 或 `DB_PASSWORD` 等环境变量传递凭据。

## Python API

```python
from db_tools import build_config, create_engine_from_config, execute_query

config = build_config(
    driver="postgresql",
    host="localhost",
    database="mydb",
    query={"sslmode": "require"},
)
engine = create_engine_from_config(config)

with engine.connect() as conn:
    result = execute_query(conn, "SELECT * FROM users")
    print(result)
```

## 测试

```bash
pytest
```

## 设计说明

- `db_tools/` 作为原生 Python 库，尽量暴露 SQLAlchemy 原生对象（`Engine`、`Connection`、`Inspector`）。
- `scripts/main.py` 仅负责参数解析、命令分发与结果序列化。
- 连接 URL 中的密码等敏感信息不会写入 stdout/stderr。
