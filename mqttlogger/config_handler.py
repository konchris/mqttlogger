#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import argparse
import logging
import json
import os


module_logger = logging.getLogger("mqttlogger.configuration_handler")


def parse_agruments(args):
    """The argument parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conf", help="path to config file")
    parser.add_argument('--debug', help='set logging trace level to debug', action='store_true')
    return parser.parse_args(args)


class ConfigData:
    """ class for managing application configuration settings """

    def __init__(self, log_level=logging.INFO):
        self.log_level = log_level
        self.config_path = ""
        self.config_dict = {}
        self.db_connect_string = ""

    def load_config_file(self, config_path):
        assert os.path.exists(config_path)
        self.config_path = config_path
        config_file = open(self.config_path, "r")
        self.config_dict = json.load(config_file)
        config_file.close()

    def create_db_connect_string(self):
        """Create the db connection string"""
        self.db_connect_string = f"mysql+mysqldb://{self.config_dict['user']}:{self.config_dict['password']}@" \
                                 f"{self.config_dict['ip']}:{self.config_dict['port']}/{self.config_dict['database']}"


def main(argv=None):
    """The main function"""
    arguments = parse_agruments(argv)

    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = ConfigData()
    config.load_config_file(arguments.conf)
    config.create_db_connect_string()

    print(config.db_connect_string)

    return 0


if __name__ == '__main__':
    import sys

    sys.exit(main(sys.argv[1:]))
