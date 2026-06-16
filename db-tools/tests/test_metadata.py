import pytest
import sqlalchemy

from db_tools.metadata import get_inspector, list_tables, get_columns


@pytest.fixture
def sqlite_engine():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(sqlalchemy.text("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER)"))
        conn.commit()
    return engine


def test_get_inspector(sqlite_engine):
    inspector = get_inspector(sqlite_engine)
    assert inspector is not None


def test_list_tables(sqlite_engine):
    tables = list_tables(sqlite_engine)
    assert "users" in tables
    assert "orders" in tables


def test_list_tables_with_inspector(sqlite_engine):
    inspector = get_inspector(sqlite_engine)
    tables = list_tables(inspector)
    assert "users" in tables


def test_get_columns(sqlite_engine):
    columns = get_columns(sqlite_engine, "users")
    names = [c["name"] for c in columns]
    assert "id" in names
    assert "name" in names


def test_get_columns_generic_types(sqlite_engine):
    columns = get_columns(sqlite_engine, "users", generic_types=True)
    assert all("type" in c for c in columns)
