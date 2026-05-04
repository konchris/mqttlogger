#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import json
import logging
import pathlib

module_logger = logging.getLogger("mqttloger.db_connection")


def load_config_file(config_path: pathlib.Path) -> dict:
    """Wrapper around json to load a configuration file as a dictionary

    Parameters
    ----------
    config_path: str
        The absolute path to the configuration file to load.

    Returns
    -------
    config_data: dict

    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)  # raises json.JSONDecodeError on malformed JSON

    required_keys = {
        "mqtt_server_ip", "mqtt_server_port",
        "db_ip", "db_port", "db_user", "db_password", "db_database",
    }
    missing = required_keys - config_data.keys()
    if missing:
        raise KeyError(
            f"Configuration file {config_path} is missing required key(s): "
            + ", ".join(sorted(missing))
        )

    return config_data


def create_connection_string(config_path: pathlib.Path) -> str:
    """Generate connection URL for the database from the configuration file.

    Parameters
    ----------
    config_path: str
        The absolute path to the database configuration file.

    Returns
    -------
    db_url : str
        the connection string
    """
    config_data = load_config_file(config_path)
    db_url = "mysql+mysqldb://{u}:{pwd}@{ip}:{prt}/{db}".format(u=config_data["db_user"],
                                                                pwd=config_data["db_password"],
                                                                ip=config_data["db_ip"], prt=config_data["db_port"],
                                                                db=config_data["db_database"])
    return db_url
