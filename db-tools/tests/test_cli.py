import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "main.py"
REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(args):
    cmd = [sys.executable, str(SCRIPT)] + args
    env = {"PYTHONPATH": str(REPO_ROOT)}
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


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only behavior")
def test_cli_sets_openssl_conf_before_sqlalchemy(tmp_path):
    """CLI must set OPENSSL_CONF before sqlalchemy is imported for mssql+pyodbc."""
    probe = tmp_path / "probe.py"
    probe.write_text(dedent("""
        import sys, os, builtins, runpy
        os.environ.pop('OPENSSL_CONF', None)
        _orig = builtins.__import__
        def _spy(name, *args, **kwargs):
            if name == 'sqlalchemy':
                sys.exit(0 if os.environ.get('OPENSSL_CONF') else 1)
            return _orig(name, *args, **kwargs)
        builtins.__import__ = _spy
        script = sys.argv[1]
        sys.argv = [script] + sys.argv[2:]
        runpy.run_path(script, run_name='__main__')
    """))
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    result = subprocess.run(
        [sys.executable, str(probe), str(SCRIPT), "--driver", "mssql+pyodbc", "test"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, (
        f"OPENSSL_CONF not set before sqlalchemy import.\\nstderr: {result.stderr}"
    )
