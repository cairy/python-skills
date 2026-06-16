"""SQL execution and result serialization for db-tools."""

import decimal
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.engine.cursor import CursorResult

from db_tools.core import ReadOnlyError


def is_read_only_sql(sql: str) -> bool:
    """Return True if the SQL statement is a read-only SELECT.

    Args:
        sql: Raw SQL string to inspect.

    Returns:
        True when the trimmed statement starts with ``select`` (case-insensitive)
        and does not contain ``into`` (case-insensitive).
    """
    stripped = sql.strip().lower()
    return stripped.startswith("select") and "into" not in stripped


def execute_raw(
    conn: Connection,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
) -> CursorResult[Any]:
    """Execute raw SQL and return the native SQLAlchemy result object.

    Args:
        conn: An open SQLAlchemy connection.
        sql: Raw SQL string.
        params: Optional bind parameters forwarded to ``text().bindparams()``.

    Returns:
        The SQLAlchemy ``CursorResult``.
    """
    stmt = sqlalchemy.text(sql)
    if params:
        stmt = stmt.bindparams(**params)
    return conn.execute(stmt)


def _prepare_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert special Python types to strings for database binding.

    SQLite (and some other drivers) do not natively preserve ``Decimal``,
    ``datetime``, or ``date`` values. Converting them to strings before
    binding ensures they round-trip in a JSON-serializable form.

    Args:
        params: Original bind parameters.

    Returns:
        Parameters with special types converted to strings.
    """
    if not params:
        return params
    prepared: Dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, decimal.Decimal):
            prepared[key] = str(value)
        elif isinstance(value, datetime):
            prepared[key] = value.isoformat()
        elif isinstance(value, date) and not isinstance(value, datetime):
            prepared[key] = value.isoformat()
        else:
            prepared[key] = value
    return prepared


def _describe_columns(result: CursorResult[Any]) -> List[Dict[str, str]]:
    """Extract column metadata from a SQLAlchemy result.

    Args:
        result: A SQLAlchemy ``CursorResult``.

    Returns:
        List of dicts with ``name`` and ``type`` keys.
    """
    columns = []
    for key in result.keys():
        columns.append({"name": key, "type": "UNKNOWN"})
    return columns


def _serialize_value(value: Any) -> Any:
    """Convert a single value to a JSON-serializable form.

    Handles ``Decimal``, ``datetime``, ``date``, and ``bytes``.

    Args:
        value: A value from a SQLAlchemy row.

    Returns:
        JSON-friendly representation of the value.
    """
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _fetch_rows(
    result: CursorResult[Any],
    limit: Optional[int] = None,
) -> tuple[List[List[Any]], int, bool]:
    """Fetch rows from a result, applying an optional row limit.

    Args:
        result: A SQLAlchemy ``CursorResult``.
        limit: Maximum number of rows to return.

    Returns:
        Tuple of ``(rows, row_count, truncated)``.
    """
    rows: List[List[Any]] = []
    truncated = False
    for row in result:
        if limit is not None and len(rows) >= limit:
            truncated = True
            break
        rows.append([_serialize_value(v) for v in row])
    return rows, len(rows), truncated


def execute_query(
    conn: Connection,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    read_only: bool = False,
) -> Dict[str, Any]:
    """Execute SQL and return a serialized, JSON-friendly result dict.

    Args:
        conn: An open SQLAlchemy connection.
        sql: Raw SQL string.
        params: Optional bind parameters.
        limit: Maximum number of rows to return for SELECT statements.
        read_only: If ``True``, raises ``ReadOnlyError`` for non-SELECT statements.

    Returns:
        For SELECT queries: ``{"columns": [...], "rows": [...], "row_count": int,
        "truncated": bool, "affected_rows": None}``.
        For other queries: ``{"affected_rows": int}``.

    Raises:
        ReadOnlyError: If ``read_only`` is ``True`` and the SQL is not a read-only SELECT.
    """
    if read_only and not is_read_only_sql(sql):
        raise ReadOnlyError("Write operation blocked in read-only mode.")

    prepared_params = _prepare_params(params)
    result = execute_raw(conn, sql, prepared_params)

    if not is_read_only_sql(sql):
        conn.commit()
        return {"affected_rows": result.rowcount}

    columns = _describe_columns(result)
    rows, row_count, truncated = _fetch_rows(result, limit)
    return {
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "truncated": truncated,
        "affected_rows": None,
    }
