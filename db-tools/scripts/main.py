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
import sys
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from db_tools.config import build_config, build_config_from_url, load_env_file
from db_tools.core import ConnectionConfig, ReadOnlyError
from db_tools.engine import create_engine_from_config
from db_tools.metadata import get_columns, get_inspector, list_tables
from db_tools.query import execute_query, is_read_only_sql


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
        _output_success(result)
        return 0
    except Exception as exc:
        _output_error("Query failed", exc)
        return 1


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
