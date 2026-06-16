from dataclasses import asdict

import pytest

from db_tools.core import ConnectionConfig, ConfigurationError, DriverNotFoundError, ReadOnlyError


def test_connection_config_defaults():
    cfg = ConnectionConfig(driver="sqlite", database=":memory:")
    assert cfg.host is None
    assert cfg.port is None
    assert cfg.username is None
    assert cfg.password is None
    assert cfg.query == {}
    assert cfg.app_name is None
    assert cfg.oracle_client_enabled is False
    assert cfg.oracle_client_path is None
    assert cfg.oracle_tns_enabled is False
    assert cfg.oracle_tns_path is None


def test_connection_config_asdict():
    cfg = ConnectionConfig(driver="postgresql", host="localhost", port=5432, database="db")
    d = asdict(cfg)
    assert d["driver"] == "postgresql"
    assert d["host"] == "localhost"
    assert d["port"] == 5432
    assert d["database"] == "db"
    assert d["query"] == {}


def test_configuration_error():
    with pytest.raises(ConfigurationError, match="missing driver"):
        raise ConfigurationError("missing driver")


def test_read_only_error():
    with pytest.raises(ReadOnlyError):
        raise ReadOnlyError("write not allowed")


def test_driver_not_found_error():
    with pytest.raises(DriverNotFoundError):
        raise DriverNotFoundError("driver missing")
