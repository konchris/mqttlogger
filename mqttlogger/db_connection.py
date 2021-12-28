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
    assert config_path.exists()
    config_file = open(config_path, 'r')
    config_data = json.load(config_file)
    config_file.close()
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
