#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import pytest

from mqttlogger.db_connection import load_config_file


def test_missing_config_file_raises(tmp_path):
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config_file(missing)


def test_malformed_json_raises(tmp_path):
    bad_config = tmp_path / "config.json"
    bad_config.write_text("not valid json {{{")
    with pytest.raises(json.JSONDecodeError):
        load_config_file(bad_config)


def test_missing_required_key_raises(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"mqtt_server_ip": "localhost"}))
    with pytest.raises(KeyError, match="missing required key"):
        load_config_file(config)
