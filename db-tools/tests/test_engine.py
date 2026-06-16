"""Tests for SQLAlchemy engine creation."""

from unittest.mock import patch

import pytest
import sqlalchemy

from db_tools.core import ConnectionConfig, DriverNotFoundError
from db_tools.engine import create_engine_from_config


def test_create_sqlite_engine():
    cfg = ConnectionConfig(driver="sqlite", database=":memory:")
    engine = create_engine_from_config(cfg)
    assert isinstance(engine, sqlalchemy.Engine)
    assert str(engine.url) == "sqlite:///:memory:"


def test_create_postgresql_engine_url():
    cfg = ConnectionConfig(
        driver="postgresql",
        host="localhost",
        port=5432,
        database="mydb",
        username="user",
        password="pass",
    )
    engine = create_engine_from_config(cfg)
    assert engine.url.drivername == "postgresql"
    assert engine.url.host == "localhost"
    assert engine.url.database == "mydb"


def test_sqlserver_odbc_driver_injected():
    cfg = ConnectionConfig(driver="mssql+pyodbc", host="localhost", database="db")
    with patch("db_tools.engine.find_sqlserver_driver", return_value="ODBC Driver 18 for SQL Server"):
        engine = create_engine_from_config(cfg)
    assert engine.url.query.get("driver") == "ODBC Driver 18 for SQL Server"


def test_sqlserver_missing_driver_raises_on_posix():
    cfg = ConnectionConfig(driver="mssql+pyodbc", host="localhost", database="db")
    with patch("db_tools.engine.find_sqlserver_driver", return_value=""):
        with patch("db_tools.engine.os.name", "posix"):
            with pytest.raises(DriverNotFoundError, match="No SQL Server ODBC driver found"):
                create_engine_from_config(cfg)


def test_oracle_client_init():
    cfg = ConnectionConfig(
        driver="oracle+oracledb",
        host="localhost",
        database="XE",
        username="user",
        password="pass",
        oracle_client_enabled=True,
        oracle_client_path="/opt/oracle/instantclient",
    )
    with patch("db_tools.engine.oracledb") as mock_oracledb:
        engine = create_engine_from_config(cfg)
    mock_oracledb.init_oracle_client.assert_called_once_with("/opt/oracle/instantclient")
