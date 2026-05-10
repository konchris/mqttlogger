import json
import pathlib
import pytest

from mqttlogger.db_connection import load_config_file, create_connection_string

VALID_CONFIG = {
    "mqtt_server_ip": "localhost",
    "mqtt_server_port": 1883,
    "db_ip": "localhost",
    "db_port": 3306,
    "db_user": "testuser",
    "db_password": "testpass",
    "db_database": "testdb",
}


def _write_config(tmp_path, data):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data))
    return p


def test_load_valid_config(tmp_path):
    p = _write_config(tmp_path, VALID_CONFIG)
    result = load_config_file(p)
    assert result["db_user"] == "testuser"
    assert result["mqtt_server_ip"] == "localhost"


def test_load_missing_file():
    with pytest.raises(FileNotFoundError) as exc_info:
        load_config_file(pathlib.Path("/nonexistent/config.json"))
    assert "config.json" in str(exc_info.value)


def test_load_missing_keys_names_them(tmp_path):
    p = _write_config(tmp_path, {"mqtt_server_ip": "localhost"})
    with pytest.raises(KeyError) as exc_info:
        load_config_file(p)
    # Error message must name at least one missing key (NFR-USE-001)
    error_text = str(exc_info.value)
    assert any(k in error_text for k in ("db_ip", "db_user", "db_password", "db_database"))


def test_load_malformed_json(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{ not valid json }")
    with pytest.raises(json.JSONDecodeError):
        load_config_file(p)


def test_load_returns_all_keys(tmp_path):
    p = _write_config(tmp_path, VALID_CONFIG)
    result = load_config_file(p)
    for key in VALID_CONFIG:
        assert key in result


def test_create_connection_string_format(tmp_path):
    p = _write_config(tmp_path, VALID_CONFIG)
    url = create_connection_string(p)
    assert "testuser" in url
    assert "localhost" in url
    assert "3306" in url
    assert "testdb" in url


def test_create_connection_string_starts_with_mysql(tmp_path):
    p = _write_config(tmp_path, VALID_CONFIG)
    url = create_connection_string(p)
    assert url.startswith("mysql+")
