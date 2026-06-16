"""SQLAlchemy engine creation from ConnectionConfig."""

import os
from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL

from db_tools.config import apply_macos_sqlserver_openssl_workaround
from db_tools.core import ConnectionConfig, DriverNotFoundError
from db_tools.drivers import find_sqlserver_driver

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None  # type: ignore[assignment]


def create_engine_from_config(config: ConnectionConfig, **kwargs: Any) -> Engine:
    """Create a SQLAlchemy Engine from a ConnectionConfig.

    Args:
        config: The connection configuration.
        **kwargs: Additional arguments passed to ``sqlalchemy.create_engine``.

    Returns:
        A SQLAlchemy Engine instance.
    """
    apply_macos_sqlserver_openssl_workaround(config)

    query: Dict[str, str] = dict(config.query)

    if config.driver == "mssql+pyodbc":
        _configure_sqlserver(config, query, kwargs)
    elif config.driver == "oracle+oracledb":
        _configure_oracle(config, kwargs)

    url = URL.create(
        drivername=config.driver,
        username=config.username,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.database,
        query=query,
    )

    return create_engine(url, **kwargs)


def _configure_sqlserver(config: ConnectionConfig, query: Dict[str, str], kwargs: Dict[str, Any]) -> None:
    """Configure SQL Server-specific settings for pyodbc.

    Args:
        config: The connection configuration.
        query: Mutable URL query parameters.
        kwargs: Mutable keyword arguments for ``create_engine``.
    """
    if config.app_name is not None:
        query["App"] = config.app_name

    driver = query.get("driver") or find_sqlserver_driver()

    if os.name == "nt" and not driver:
        raise DriverNotFoundError("No SQL Server ODBC driver found.")

    if driver:
        query["driver"] = driver
        kwargs.setdefault("fast_executemany", True)

        if os.name != "nt" and driver.startswith("ODBC Driver"):
            try:
                version = int(driver.split()[2])
            except (IndexError, ValueError):
                version = 0
            if version >= 18:
                connect_args = kwargs.setdefault("connect_args", {})
                connect_args.setdefault("Encrypt", "no")
                connect_args.setdefault("TrustServerCertificate", "yes")
    else:
        # posix fallback
        query["driver"] = "/usr/local/lib/libtdsodbc.so"
        if config.port is None:
            query.setdefault("port", "1433")


def _configure_oracle(config: ConnectionConfig, kwargs: Dict[str, Any]) -> None:
    """Configure Oracle-specific settings for oracledb.

    Args:
        config: The connection configuration.
        kwargs: Mutable keyword arguments for ``create_engine``.
    """
    if config.oracle_client_enabled and oracledb is not None:
        oracledb.init_oracle_client(config.oracle_client_path)

    if config.oracle_tns_enabled and oracledb is not None:
        if not config.oracle_client_enabled:
            connect_args = kwargs.setdefault("connect_args", {})
            connect_args.setdefault("config_dir", config.oracle_tns_path)
