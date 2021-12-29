#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import argparse
import logging


def parse_agruments(args):
    """The argument parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help='set logging trace level to debug', action='store_true')
    return parser.parse_args(args)


def main(argv=None):
    """The main function"""
    arguments = parse_agruments(argv)

    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    return 0


if __name__ == '__main__':
    import sys

    sys.exit(main(sys.argv[1:]))
