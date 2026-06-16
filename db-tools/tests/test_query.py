import decimal
from datetime import date, datetime

import pytest
import sqlalchemy

from db_tools.core import ReadOnlyError
from db_tools.query import execute_query, execute_raw, is_read_only_sql


@pytest.fixture
def sqlite_conn():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(sqlalchemy.text("INSERT INTO users (id, name) VALUES (1, 'alice')"))
        conn.execute(sqlalchemy.text("INSERT INTO users (id, name) VALUES (2, 'bob')"))
        conn.commit()
        yield conn


def test_is_read_only_sql():
    assert is_read_only_sql("SELECT * FROM users") is True
    assert is_read_only_sql("  select id from users  ") is True
    assert is_read_only_sql("INSERT INTO users VALUES (1)") is False
    assert is_read_only_sql("UPDATE users SET name='x'") is False
    assert is_read_only_sql("DELETE FROM users") is False
    assert is_read_only_sql("CREATE TABLE t (id INT)") is False


def test_execute_raw(sqlite_conn):
    result = execute_raw(sqlite_conn, "SELECT * FROM users ORDER BY id")
    rows = result.fetchall()
    assert len(rows) == 2
    assert rows[0][0] == 1


def test_execute_query_select(sqlite_conn):
    result = execute_query(sqlite_conn, "SELECT * FROM users ORDER BY id")
    assert result["row_count"] == 2
    assert len(result["columns"]) == 2
    assert result["columns"][0]["name"] == "id"
    assert result["rows"][0] == [1, "alice"]
    assert result["truncated"] is False


def test_execute_query_with_limit(sqlite_conn):
    result = execute_query(sqlite_conn, "SELECT * FROM users ORDER BY id", limit=1)
    assert result["row_count"] == 1
    assert result["truncated"] is True


def test_execute_query_with_params(sqlite_conn):
    result = execute_query(sqlite_conn, "SELECT * FROM users WHERE id = :id", params={"id": 2})
    assert result["row_count"] == 1
    assert result["rows"][0][1] == "bob"


def test_execute_query_insert(sqlite_conn):
    result = execute_query(sqlite_conn, "INSERT INTO users (id, name) VALUES (3, 'carol')")
    assert result["affected_rows"] == 1


def test_read_only_blocks_write():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        conn.commit()
        for statement in [
            "INSERT INTO users (id) VALUES (1)",
            "UPDATE users SET id = 2",
            "DELETE FROM users",
            "DROP TABLE users",
        ]:
            with pytest.raises(ReadOnlyError):
                execute_query(conn, statement, read_only=True)


def test_execute_query_limit_zero(sqlite_conn):
    result = execute_query(sqlite_conn, "SELECT * FROM users ORDER BY id", limit=0)
    assert result["row_count"] == 0
    assert result["rows"] == []
    assert result["truncated"] is True


def test_execute_query_affected_rows_none(sqlite_conn):
    result = execute_query(sqlite_conn, "SELECT * FROM users ORDER BY id")
    assert result["affected_rows"] is None


def test_serialize_bytes(sqlite_conn):
    result = execute_query(sqlite_conn, "SELECT CAST('hello' AS BLOB) AS data")
    assert result["rows"][0] == ["hello"]


def test_serialize_special_types(sqlite_conn):
    result = execute_query(
        sqlite_conn,
        "SELECT :dec AS dec, :dt AS dt, :d AS d",
        params={"dec": decimal.Decimal("1.23"), "dt": datetime(2024, 1, 1, 12, 0), "d": date(2024, 1, 1)},
    )
    assert result["rows"][0] == ["1.23", "2024-01-01T12:00:00", "2024-01-01"]
