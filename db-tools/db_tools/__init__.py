"""db-tools public API."""

from db_tools.core import (
    ConnectionConfig,
    ConfigurationError,
    DriverNotFoundError,
    ReadOnlyError,
)
from db_tools.config import (
    build_config,
    build_config_from_url,
    load_env_file,
    setup_openssl_legacy,
)

__all__ = [
    "ConnectionConfig",
    "ConfigurationError",
    "DriverNotFoundError",
    "ReadOnlyError",
    "build_config",
    "build_config_from_url",
    "load_env_file",
    "setup_openssl_legacy",
    "create_engine_from_config",
    "execute_query",
    "execute_raw",
    "is_read_only_sql",
    "get_inspector",
    "list_tables",
    "get_columns",
]


def __getattr__(name: str):
    """Lazy-load engine, query and metadata submodules on first access."""
    if name == "create_engine_from_config":
        from db_tools.engine import create_engine_from_config
        return create_engine_from_config
    if name in ("execute_query", "execute_raw", "is_read_only_sql"):
        from db_tools import query
        return getattr(query, name)
    if name in ("get_inspector", "list_tables", "get_columns"):
        from db_tools import metadata
        return getattr(metadata, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
