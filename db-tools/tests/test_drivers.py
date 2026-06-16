from unittest.mock import patch

import pytest

from db_tools.drivers import DriverName, find_sqlserver_driver, list_odbc_drivers


def test_driver_name_enum():
    assert DriverName.POSTGRESQL == "postgresql"
    assert DriverName.MYSQL == "mysql+mysqldb"
    assert DriverName.SQLSERVER == "mssql+pyodbc"
    assert DriverName.ORACLE == "oracle+oracledb"
    assert DriverName.SQLITE == "sqlite"


def test_list_odbc_drivers():
    with patch("db_tools.drivers.pyodbc") as mock_pyodbc:
        mock_pyodbc.drivers.return_value = ["ODBC Driver 17 for SQL Server"]
        assert list_odbc_drivers() == ["ODBC Driver 17 for SQL Server"]


def test_find_sqlserver_driver_prefers_odbc_driver():
    with patch("db_tools.drivers.pyodbc") as mock_pyodbc:
        mock_pyodbc.drivers.return_value = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 18 for SQL Server",
            "SQL Server Native Client 11.0",
        ]
        assert find_sqlserver_driver() == "ODBC Driver 18 for SQL Server"


def test_find_sqlserver_driver_falls_back_to_native_client():
    with patch("db_tools.drivers.pyodbc") as mock_pyodbc:
        mock_pyodbc.drivers.return_value = ["SQL Server Native Client 11.0"]
        assert find_sqlserver_driver() == "SQL Server Native Client 11.0"


def test_find_sqlserver_driver_not_found():
    with patch("db_tools.drivers.pyodbc") as mock_pyodbc:
        mock_pyodbc.drivers.return_value = ["Some Other Driver"]
        assert find_sqlserver_driver() == ""
