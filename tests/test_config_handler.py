#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import os
import json

import pytest

from mqttlogger.config_handler import ConfigData


@pytest.fixture()
def config_path():
    """Path to local config file"""
    return os.path.join("..", "config.json")


@pytest.fixture()
def test_config():
    """Dummy DB configuration file contents"""
    test_config_dict = {"ip": "127.0.0.1",
                        "port": "3306",
                        "user": "mqttlogger",
                        "password": "REDACTED_DB_PASS",
                        "database": "sensorreadings"}
    return test_config_dict


@pytest.fixture(scope="module")
def config_data_instance():
    config_data = ConfigData()
    yield config_data


@pytest.fixture()
def test_db_connect_string():
    yield "mysql+mysqldb://mqttlogger:REDACTED_DB_PASS@127.0.0.1:3306/sensorreadings"


def test_load_config_file(mocker, config_path, test_config, config_data_instance):
    mocker.patch("mqttlogger.config_handler.open")
    mocker.patch("json.load", return_value=test_config)

    config_data_instance.load_config_file(config_path)

    json.load.assert_called_once()

    assert config_data_instance.config_dict == test_config


def test_create_db_connect_string(test_db_connect_string, mocker, config_data_instance):

    config_data_instance.create_db_connect_string()

    assert config_data_instance.db_connect_string == test_db_connect_string

