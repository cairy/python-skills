# db-tools

跨数据库连接、查询与元数据探查工具，基于 SQLAlchemy。

## 安装

```bash
pip install -e .
```

## CLI 用法

```bash
python scripts/main.py --driver sqlite --database :memory: test
python scripts/main.py --driver sqlite --database :memory: query "SELECT 1"
```

## Python API

```python
from db_tools import build_config, create_engine_from_config, execute_query

config = build_config(driver="postgresql", host="localhost", database="mydb")
engine = create_engine_from_config(config)

with engine.connect() as conn:
    print(execute_query(conn, "SELECT * FROM users"))
```

## 测试

```bash
pytest
```
