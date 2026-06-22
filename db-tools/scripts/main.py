# /// script
# dependencies = [
#   "sqlalchemy>=2.0",
#   "pyodbc>=4.0; platform_system!='Linux'",
# ]
# requires-python = ">=3.10"
# ///

"""db-tools CLI entry point."""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow the script to find db_tools when run directly without installing the package.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))


def _bundled_openssl_conf_path() -> Path:
    """Return path to the bundled OpenSSL legacy config without importing db_tools."""
    return _SCRIPT_DIR.parent / "db_tools" / "resources" / "openssl_allow_tls1.0.cnf"


def _load_env_file_early(path: str) -> None:
    """Load environment variables from an explicit .env file (stdlib-only)."""
    env_path = Path(path)
    if not env_path.exists():
        return
    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


def _driver_from_url(url: str) -> Optional[str]:
    """Extract drivername from a SQLAlchemy URL without importing sqlalchemy."""
    if "://" not in url:
        return None
    return url.split("://", 1)[0]


def _setup_openssl_legacy_early() -> None:
    """Set OPENSSL_CONF before any third-party import if this looks like macOS SQL Server."""
    if sys.platform != "darwin":
        return
    if os.environ.get("OPENSSL_CONF"):
        return

    early_parser = argparse.ArgumentParser(add_help=False)
    early_parser.add_argument("--driver")
    early_parser.add_argument("--env-file")
    early_parser.add_argument("--url")
    early_args, _ = early_parser.parse_known_args()

    if early_args.env_file:
        _load_env_file_early(early_args.env_file)

    driver = early_args.driver or os.environ.get("DB_DRIVER")
    if not driver and early_args.url:
        driver = _driver_from_url(early_args.url)

    if driver != "mssql+pyodbc":
        return

    conf_path = _bundled_openssl_conf_path()
    if conf_path.exists():
        os.environ["OPENSSL_CONF"] = str(conf_path)


_setup_openssl_legacy_early()

# Now safe to import third-party libraries that initialise OpenSSL.
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

from db_tools.config import build_config, build_config_from_url, load_env_file  # noqa: E402
from db_tools.core import ConnectionConfig, ReadOnlyError  # noqa: E402
from db_tools.engine import create_engine_from_config  # noqa: E402
from db_tools.metadata import get_columns, get_inspector, list_tables  # noqa: E402
from db_tools.query import execute_query, is_read_only_sql  # noqa: E402


def _build_config_from_args(args: argparse.Namespace) -> ConnectionConfig:
    """Build a ConnectionConfig from CLI arguments."""
    if args.url:
        return build_config_from_url(args.url)
    return build_config(
        driver=args.driver,
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password,
        app_name=args.app_name,
    )


def _create_engine_from_args(args: argparse.Namespace) -> Engine:
    """Create a SQLAlchemy Engine from CLI arguments."""
    if args.env_file:
        load_env_file(args.env_file)
    config = _build_config_from_args(args)
    return create_engine_from_config(config)


def _output_success(data: Any) -> None:
    """Print success JSON to stdout."""
    print(json.dumps({"success": True, "data": data}, indent=2))


def _output_error(message: str, exc: Optional[Exception] = None) -> None:
    """Print human-readable text and JSON error to stderr."""
    if exc is not None:
        print(f"{message}: {exc}", file=sys.stderr)
    else:
        print(message, file=sys.stderr)
    error_data: Dict[str, Any] = {"success": False, "error": message}
    if exc is not None:
        error_data["error_type"] = type(exc).__name__
    print(json.dumps(error_data), file=sys.stderr)


def cmd_test(args: argparse.Namespace) -> int:
    """Test database connection and return status info."""
    try:
        engine = _create_engine_from_args(args)
        start = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        _output_success(
            {
                "connected": True,
                "driver": engine.url.drivername,
                "server_version": engine.dialect.server_version_info,
                "latency_ms": round(latency_ms, 2),
            }
        )
        return 0
    except Exception as exc:
        _output_error("Connection failed", exc)
        return 1


def cmd_query(args: argparse.Namespace) -> int:
    """Execute a SQL query and return results."""
    try:
        engine = _create_engine_from_args(args)
        sql = args.sql
        read_only = not args.allow_write
        if read_only and not is_read_only_sql(sql):
            raise ReadOnlyError("Write operation blocked in read-only mode.")

        params: Optional[Dict[str, Any]] = None
        if args.params:
            params = json.loads(args.params)

        with engine.connect() as conn:
            result = execute_query(
                conn,
                sql,
                params=params,
                limit=args.limit,
                read_only=read_only,
            )
        if args.format == "table":
            result["rows"] = _format_table(result["columns"], result["rows"])
        _output_success(result)
        return 0
    except Exception as exc:
        _output_error("Query failed", exc)
        return 1


def _format_table(columns: List[Dict[str, str]], rows: List[List[Any]]) -> str:
    """Format query results as a simple text table."""
    if not columns:
        return ""
    headers = [c["name"] for c in columns]
    widths = [len(h) for h in headers]
    rendered_rows: List[List[str]] = []
    for row in rows:
        rendered = [str(v) if v is not None else "NULL" for v in row]
        rendered_rows.append(rendered)
        widths = [max(widths[i], len(rendered[i])) for i in range(len(headers))]

    lines = [
        " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)),
        "-+-".join("-" * widths[i] for i in range(len(headers))),
    ]
    for rendered in rendered_rows:
        lines.append(" | ".join(rendered[i].ljust(widths[i]) for i in range(len(headers))))
    return "\n".join(lines)


def cmd_tables(args: argparse.Namespace) -> int:
    """List tables in the database."""
    try:
        engine = _create_engine_from_args(args)
        inspector = get_inspector(engine)
        tables = list_tables(inspector, schema=args.schema)
        _output_success(tables)
        return 0
    except Exception as exc:
        _output_error("Failed to list tables", exc)
        return 1


def cmd_columns(args: argparse.Namespace) -> int:
    """List columns for a given table."""
    try:
        engine = _create_engine_from_args(args)
        inspector = get_inspector(engine)
        columns = get_columns(
            inspector,
            table_name=args.table,
            schema=args.schema,
            generic_types=args.generic_types,
        )
        _output_success(columns)
        return 0
    except Exception as exc:
        _output_error("Failed to list columns", exc)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Database connection and query tool")
    # Global connection arguments
    parser.add_argument("--driver", help="Database driver")
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--port", type=int, help="Database port")
    parser.add_argument("--database", help="Database name")
    parser.add_argument("--username", help="Database username")
    parser.add_argument("--password", help="Database password")
    parser.add_argument("--url", help="Full SQLAlchemy connection URL")
    parser.add_argument("--env-file", help="Path to .env file to load")
    parser.add_argument("--app-name", help="Application name for connection")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # test subcommand
    subparsers.add_parser("test", help="Test database connection")

    # query subcommand
    query_parser = subparsers.add_parser("query", help="Execute SQL query")
    query_parser.add_argument("sql", help="SQL statement to execute")
    query_parser.add_argument("--params", help="JSON-encoded query parameters")
    query_parser.add_argument(
        "--limit", type=int, default=1000, help="Maximum rows to return (default: 1000)"
    )
    query_parser.add_argument(
        "--format", choices=["json", "table"], default="json", help="Output format"
    )
    query_parser.add_argument(
        "--allow-write", action="store_true", help="Allow write operations (DML/DDL)"
    )

    # tables subcommand
    tables_parser = subparsers.add_parser("tables", help="List database tables")
    tables_parser.add_argument("--schema", help="Schema to filter tables")

    # columns subcommand
    columns_parser = subparsers.add_parser("columns", help="List columns for a table")
    columns_parser.add_argument("table", help="Table name")
    columns_parser.add_argument("--schema", help="Schema name")
    columns_parser.add_argument(
        "--generic-types", action="store_true", help="Use generic SQL types"
    )

    args = parser.parse_args()

    if args.command == "test":
        return cmd_test(args)
    if args.command == "query":
        return cmd_query(args)
    if args.command == "tables":
        return cmd_tables(args)
    if args.command == "columns":
        return cmd_columns(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
