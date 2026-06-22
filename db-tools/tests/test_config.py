import os
from pathlib import Path
from unittest.mock import patch

import pytest

from db_tools.config import (
    build_config,
    build_config_from_url,
    load_env_file,
    setup_openssl_legacy,
)
from db_tools.core import ConnectionConfig


def test_build_config_from_params():
    cfg = build_config(
        driver="postgresql",
        host="localhost",
        port=5432,
        database="mydb",
        username="user",
        password="pass",
    )
    assert cfg.driver == "postgresql"
    assert cfg.host == "localhost"
    assert cfg.port == 5432
    assert cfg.database == "mydb"
    assert cfg.username == "user"
    assert cfg.password == "pass"


def test_build_config_from_url():
    cfg = build_config_from_url("postgresql://user:pass@localhost:5432/mydb")
    assert cfg.driver == "postgresql"
    assert cfg.host == "localhost"
    assert cfg.port == 5432
    assert cfg.database == "mydb"
    assert cfg.username == "user"
    assert cfg.password == "pass"


def test_build_config_with_query_options():
    cfg = build_config(
        driver="postgresql",
        host="localhost",
        database="mydb",
        query={"sslmode": "require", "connect_timeout": "10"},
    )
    assert cfg.query["sslmode"] == "require"
    assert cfg.query["connect_timeout"] == "10"


def test_build_config_from_url_preserves_query():
    cfg = build_config_from_url("postgresql://user:pass@localhost:5432/mydb?sslmode=require")
    assert cfg.query["sslmode"] == "require"


def test_build_config_from_env_vars(monkeypatch):
    monkeypatch.setenv("DB_DRIVER", "mysql+mysqldb")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_DATABASE", "test")
    monkeypatch.setenv("DB_USERNAME", "root")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    cfg = build_config()
    assert cfg.driver == "mysql+mysqldb"
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 3306


def test_load_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=envhost\nDB_PORT=5432\n")
    load_env_file(str(env_file))
    assert os.environ.get("DB_HOST") == "envhost"
    assert os.environ.get("DB_PORT") == "5432"


def test_setup_openssl_legacy_sets_env_on_macos(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.delenv("OPENSSL_CONF", raising=False)
    with patch("db_tools.config._bundled_openssl_conf_path") as mock_path:
        mock_path.return_value = Path("/fake/openssl.cnf")
        with patch("pathlib.Path.exists", return_value=True):
            result = setup_openssl_legacy()
            assert result is True
            assert os.environ["OPENSSL_CONF"] == "/fake/openssl.cnf"


def test_setup_openssl_legacy_noop_on_non_macos(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("OPENSSL_CONF", raising=False)
    result = setup_openssl_legacy()
    assert result is False
    assert "OPENSSL_CONF" not in os.environ


def test_setup_openssl_legacy_noop_when_already_set(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setenv("OPENSSL_CONF", "/existing.cnf")
    result = setup_openssl_legacy()
    assert result is False
    assert os.environ["OPENSSL_CONF"] == "/existing.cnf"


def test_setup_openssl_legacy_noop_when_config_missing(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.delenv("OPENSSL_CONF", raising=False)
    with patch("db_tools.config._bundled_openssl_conf_path") as mock_path:
        mock_path.return_value = Path("/missing/openssl.cnf")
        with patch("pathlib.Path.exists", return_value=False):
            result = setup_openssl_legacy()
            assert result is False
            assert "OPENSSL_CONF" not in os.environ
