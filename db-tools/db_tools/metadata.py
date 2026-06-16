from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Engine, Inspector, inspect


def get_inspector(engine: Engine) -> Inspector:
    """Return an Inspector for the given engine."""
    return inspect(engine)


def _ensure_inspector(engine_or_inspector: Union[Engine, Inspector]) -> Inspector:
    """Return an Inspector as-is, or create one from an Engine."""
    if isinstance(engine_or_inspector, Inspector):
        return engine_or_inspector
    return get_inspector(engine_or_inspector)


def list_tables(
    engine_or_inspector: Union[Engine, Inspector],
    schema: Optional[str] = None,
) -> List[str]:
    """Return a list of table names for the given engine/inspector."""
    inspector = _ensure_inspector(engine_or_inspector)
    return inspector.get_table_names(schema=schema)


def get_columns(
    engine_or_inspector: Union[Engine, Inspector],
    table_name: str,
    schema: Optional[str] = None,
    generic_types: bool = False,
) -> List[Dict[str, Any]]:
    """Return column metadata for a table.

    Args:
        engine_or_inspector: SQLAlchemy Engine or Inspector.
        table_name: Name of the table to introspect.
        schema: Optional schema name.
        generic_types: If True, convert dialect-specific types to generic
            equivalents using ``as_generic()`` before stringifying.

    Returns:
        List of column dictionaries with ``type`` set to a string representation.
    """
    inspector = _ensure_inspector(engine_or_inspector)
    columns = inspector.get_columns(table_name, schema=schema)
    for col in columns:
        col_type = col.get("type")
        if col_type is not None:
            if generic_types and hasattr(col_type, "as_generic"):
                col_type = col_type.as_generic()
            col["type"] = str(col_type)
    return columns
