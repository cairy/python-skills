import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "main.py"


def run_cli(args):
    cmd = [sys.executable, str(SCRIPT)] + args
    env = {"PYTHONPATH": str(SCRIPT.parents[1])}
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_cli_help():
    result = run_cli(["--help"])
    assert result.returncode == 0
    assert "query" in result.stdout


def test_cli_sqlite_test():
    result = run_cli(["--driver", "sqlite", "--database", ":memory:", "test"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert data["data"]["connected"] is True


def test_cli_query_read_only_blocks_insert():
    result = run_cli([
        "--driver", "sqlite", "--database", ":memory:",
        "query", "INSERT INTO t (id) VALUES (1)",
    ])
    assert result.returncode == 1
    assert "ReadOnlyError" in result.stderr


def test_cli_query_with_allow_write():
    result = run_cli([
        "--driver", "sqlite", "--database", ":memory:",
        "query", "CREATE TABLE t (id INTEGER)",
        "--allow-write",
    ])
    assert result.returncode == 0


def test_cli_query_with_params():
    result = run_cli([
        "--driver", "sqlite", "--database", ":memory:",
        "query", "SELECT :x AS x", "--params", '{"x": 42}',
    ])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["data"]["rows"][0] == [42]


def test_cli_query_table_format():
    result = run_cli([
        "--driver", "sqlite", "--database", ":memory:",
        "query", "SELECT 1 AS id, 'alice' AS name", "--format", "table",
    ])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "id" in data["data"]["rows"]
    assert "alice" in data["data"]["rows"]


def test_cli_tables_and_columns(tmp_path):
    db_path = tmp_path / "test.db"
    result = run_cli([
        "--driver", "sqlite", "--database", str(db_path),
        "query", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
        "--allow-write",
    ])
    assert result.returncode == 0

    result = run_cli(["--driver", "sqlite", "--database", str(db_path), "tables"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "users" in data["data"]

    result = run_cli(["--driver", "sqlite", "--database", str(db_path), "columns", "users"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    names = [c["name"] for c in data["data"]]
    assert "id" in names
