"""Config building and environment utilities for db-tools."""

import os
import sys
from pathlib import Path
from typing import Optional

from db_tools.core import ConnectionConfig, ConfigurationError


def _bundled_openssl_conf_path() -> Optional[Path]:
    """Return the path to the bundled OpenSSL legacy config file."""
    try:
        from importlib.resources import files

        base = files("db_tools")
    except ImportError:  # pragma: no cover
        try:
            from importlib_resources import files  # type: ignore[no-redef,import-untyped]

            base = files("db_tools")
        except ImportError:
            return None

    try:
        path = base / "resources" / "openssl_allow_tls1.0.cnf"
        # importlib.resources.files returns a Traversable; resolve to real Path if possible
        if hasattr(path, "resolve"):
            return Path(path.resolve())
        return Path(str(path))
    except Exception:  # pragma: no cover
        return None


def load_env_file(path: str) -> None:
    """Load environment variables from an explicit .env file.

    Args:
        path: Path to the .env file.

    Raises:
        ConfigurationError: If the file does not exist.
    """
    env_path = Path(path)
    if not env_path.exists():
        raise ConfigurationError(f"Env file not found: {path}")

    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


def build_config(
    driver: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    query: Optional[dict] = None,
    app_name: Optional[str] = None,
) -> ConnectionConfig:
    """Build a ConnectionConfig from explicit parameters and environment variables.

    Explicit parameters take precedence over environment variables.

    Args:
        driver: Database driver. Env fallback: DB_DRIVER.
        host: Database host. Env fallback: DB_HOST.
        port: Database port. Env fallback: DB_PORT.
        database: Database name. Env fallback: DB_DATABASE.
        username: Username. Env fallback: DB_USERNAME.
        password: Password. Env fallback: DB_PASSWORD.
        query: Additional URL query parameters.
        app_name: Application name. Env fallback: DB_APP_NAME.

    Returns:
        A populated ConnectionConfig.

    Raises:
        ConfigurationError: If driver is missing.
    """
    resolved_driver = driver if driver is not None else os.environ.get("DB_DRIVER")
    if not resolved_driver:
        raise ConfigurationError("Database driver is required (pass driver= or set DB_DRIVER)")

    resolved_host = host if host is not None else os.environ.get("DB_HOST")
    resolved_port = port if port is not None else _int_env("DB_PORT")
    resolved_database = database if database is not None else os.environ.get("DB_DATABASE")
    resolved_username = username if username is not None else os.environ.get("DB_USERNAME")
    resolved_password = password if password is not None else os.environ.get("DB_PASSWORD")
    resolved_app_name = app_name if app_name is not None else os.environ.get("DB_APP_NAME")

    return ConnectionConfig(
        driver=resolved_driver,
        host=resolved_host,
        port=resolved_port,
        database=resolved_database,
        username=resolved_username,
        password=resolved_password,
        query=dict(query) if query else {},
        app_name=resolved_app_name,
    )


def _int_env(name: str) -> Optional[int]:
    """Return an integer from an environment variable, or None if unset/invalid."""
    val = os.environ.get(name)
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def build_config_from_url(url: str) -> ConnectionConfig:
    """Parse a SQLAlchemy URL and return a ConnectionConfig.

    Args:
        url: SQLAlchemy connection URL.

    Returns:
        A populated ConnectionConfig.

    Raises:
        ConfigurationError: If the URL cannot be parsed.
    """
    from sqlalchemy.engine.url import make_url

    try:
        parsed = make_url(url)
    except Exception as exc:
        raise ConfigurationError(f"Invalid database URL: {exc}") from exc

    driver = parsed.drivername
    host = parsed.host
    port = parsed.port
    database = parsed.database
    username = parsed.username
    password = parsed.password

    return ConnectionConfig(
        driver=driver,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        query=dict(parsed.query),
    )


def apply_macos_sqlserver_openssl_workaround(config: ConnectionConfig) -> bool:
    """Apply bundled OpenSSL config on macOS for mssql+pyodbc to allow TLS 1.0.

    Sets the OPENSSL_CONF environment variable to the bundled config path
    if running on macOS, the driver is mssql+pyodbc, and OPENSSL_CONF is not
    already set.

    Args:
        config: The connection configuration to inspect.

    Returns:
        True if the workaround was applied, False otherwise.
    """
    if sys.platform != "darwin":
        return False
    if config.driver != "mssql+pyodbc":
        return False
    if os.environ.get("OPENSSL_CONF"):
        return False

    conf_path = _bundled_openssl_conf_path()
    if conf_path is None:
        return False
    conf_path = Path(conf_path) if not isinstance(conf_path, Path) else conf_path
    if not conf_path.exists():
        return False

    os.environ["OPENSSL_CONF"] = str(conf_path)
    return True
