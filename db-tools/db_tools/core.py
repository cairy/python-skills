"""Shared infrastructure for db-tools."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ConnectionConfig:
    """Database connection configuration.

    Oracle-specific fields (``oracle_*``) are exposed explicitly because
    ``oracledb.init_oracle_client()`` must be called before creating the
    SQLAlchemy engine. Other driver-specific options (e.g. PostgreSQL
    ``sslmode``, SQL Server ``driver`` override) should be passed via
    ``query`` so they flow directly into the SQLAlchemy URL.
    """

    driver: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    query: Dict[str, str] = field(default_factory=dict)
    app_name: Optional[str] = None
    oracle_client_enabled: bool = False
    oracle_client_path: Optional[str] = None
    oracle_tns_enabled: bool = False
    oracle_tns_path: Optional[str] = None


class DbToolsError(Exception):
    """Base exception for db-tools."""


class ConfigurationError(DbToolsError):
    """Raised when connection configuration is invalid."""


class DriverNotFoundError(DbToolsError):
    """Raised when a required database driver cannot be found."""


class ReadOnlyError(DbToolsError):
    """Raised when a write operation is attempted in read-only mode."""
