"""Database driver definitions and ODBC discovery."""

import re
from enum import Enum
from typing import List


try:
    import pyodbc
except ImportError:  # pragma: no cover
    pyodbc = None  # type: ignore


class DriverName(str, Enum):
    """Supported database driver names."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql+mysqldb"
    SQLSERVER = "mssql+pyodbc"
    ORACLE = "oracle+oracledb"
    SQLITE = "sqlite"


def list_odbc_drivers() -> List[str]:
    """Return all installed ODBC drivers.

    Returns an empty list if pyodbc is not installed.
    """
    if pyodbc is None:
        return []
    return pyodbc.drivers()


def find_sqlserver_driver() -> str:
    """Find the best available SQL Server ODBC driver.

    Prefers 'ODBC Driver X for SQL Server' over 'SQL Server Native Client X.X',
    and higher version numbers over lower ones.

    Returns an empty string if no suitable driver is found.
    """
    drivers = list_odbc_drivers()
    odbc_pattern = re.compile(r"ODBC Driver\s([\d\.]+)\sfor SQL Server")
    native_pattern = re.compile(r"SQL Server Native Client\s([\d\.]+)")

    best_odbc = (0.0, "")
    best_native = (0.0, "")

    for name in drivers:
        match = odbc_pattern.fullmatch(name)
        if match:
            version = float(match.group(1))
            if version > best_odbc[0]:
                best_odbc = (version, name)
        match = native_pattern.fullmatch(name)
        if match:
            version = float(match.group(1))
            if version > best_native[0]:
                best_native = (version, name)

    if best_odbc[1]:
        return best_odbc[1]
    return best_native[1]
