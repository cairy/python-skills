"""SQL execution and result serialization for db-tools."""

import base64
import decimal
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.engine.cursor import CursorResult

from db_tools.core import ReadOnlyError


def is_read_only_sql(sql: str) -> bool:
    """Return True if the SQL statement is read-only.

    Recognizes ``SELECT``, ``WITH`` (CTE), ``EXPLAIN``, and ``VALUES`` as
    read-only statement prefixes. Rejects any string that appears to contain
    multiple statements (semicolons not at the end) or the ``INTO`` clause.

    Args:
        sql: Raw SQL string to inspect.

    Returns:
        True when the statement is a single, read-only query.
    """
    stripped = sql.strip().lower()

    # Reject multiple statements to prevent trailing writes after a SELECT.
    body = stripped.rstrip(";")
    if ";" in body:
        return False

    read_only_prefixes = ("select", "with", "explain", "values")
    if not any(body.startswith(prefix) for prefix in read_only_prefixes):
        return False

    # SELECT INTO creates a table; treat as write.
    if body.startswith("select") and "into" in body:
        return False

    return True


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
    stmt = text(sql)
    if params:
        stmt = stmt.bindparams(**params)
    return conn.execute(stmt)


def _prepare_params(
    params: Optional[Dict[str, Any]],
    dialect_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Convert special Python types for database binding when needed.

    SQLite does not natively preserve ``Decimal``, ``datetime``, or ``date``
    values, so they are converted to strings. Other dialects receive the
    original objects to preserve type information.

    Args:
        params: Original bind parameters.
        dialect_name: SQLAlchemy dialect name (e.g. ``sqlite``, ``postgresql``).
            If omitted, defaults to SQLite-compatible behavior.

    Returns:
        Parameters with special types converted when appropriate.
    """
    if not params:
        return params

    convert = dialect_name is None or dialect_name == "sqlite"
    if not convert:
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
        List of dicts with ``name`` and ``type`` keys. When the underlying
        driver does not provide a type object, ``type`` is ``"UNKNOWN"``.
    """
    keys = result.keys()
    if not keys:
        return []

    description = result.cursor.description if result.cursor else None
    columns: List[Dict[str, str]] = []
    for i, key in enumerate(keys):
        type_name = "UNKNOWN"
        if description and len(description) > i:
            type_obj = description[i][1]
            if type_obj is not None:
                if hasattr(type_obj, "__name__"):
                    type_name = type_obj.__name__
                else:
                    type_name = str(type_obj)
        columns.append({"name": key, "type": type_name})
    return columns


def _serialize_value(value: Any) -> tuple[Any, bool]:
    """Convert a single value to a JSON-serializable form.

    Handles ``Decimal``, ``datetime``, ``date``, and ``bytes``. Binary values
    are returned as base64-encoded strings.

    Args:
        value: A value from a SQLAlchemy row.

    Returns:
        Tuple of ``(serialized_value, is_binary)``.
    """
    if isinstance(value, decimal.Decimal):
        return str(value), False
    if isinstance(value, datetime):
        return value.isoformat(), False
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat(), False
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii"), True
    return value, False


def _fetch_rows(
    result: CursorResult[Any],
    limit: Optional[int] = None,
) -> tuple[List[List[Any]], int, bool, Set[int]]:
    """Fetch rows from a result, applying an optional row limit.

    Args:
        result: A SQLAlchemy ``CursorResult``.
        limit: Maximum number of rows to return.

    Returns:
        Tuple of ``(rows, row_count, truncated, binary_columns)`` where
        ``binary_columns`` is the set of column indexes that contained bytes.
    """
    rows: List[List[Any]] = []
    truncated = False
    binary_columns: Set[int] = set()
    for row in result:
        if limit is not None and len(rows) >= limit:
            truncated = True
            break
        serialized_row: List[Any] = []
        for i, value in enumerate(row):
            serialized, is_binary = _serialize_value(value)
            serialized_row.append(serialized)
            if is_binary:
                binary_columns.add(i)
        rows.append(serialized_row)
    return rows, len(rows), truncated, binary_columns


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
        For other queries: ``{"columns": [], "rows": [], "row_count": 0,
        "truncated": False, "affected_rows": int}``.

    Raises:
        ReadOnlyError: If ``read_only`` is ``True`` and the SQL is not a read-only SELECT.

    Note:
        The read-only check is a heuristic based on the statement prefix. It is
        intended to prevent accidental writes, not to provide a security boundary
        against malicious input.
    """
    select_statement = is_read_only_sql(sql)
    if read_only and not select_statement:
        raise ReadOnlyError("Write operation blocked in read-only mode.")

    prepared_params = _prepare_params(params, conn.dialect.name)
    result = execute_raw(conn, sql, prepared_params)

    if not select_statement:
        conn.commit()
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "affected_rows": result.rowcount,
        }

    columns = _describe_columns(result)
    rows, row_count, truncated, binary_columns = _fetch_rows(result, limit)
    for i in binary_columns:
        columns[i]["encoding"] = "base64"
    return {
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "truncated": truncated,
        "affected_rows": None,
    }
