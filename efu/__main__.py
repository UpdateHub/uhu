# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License


import sys

from .cliparser import CLIParser

from .upload import parser as upload_parser
from .config import parser as config_parser


subparsers = [
    config_parser,
    upload_parser,
]


def main():
    CLIParser(subparsers)
    return 0


if __name__ == '__main__':
    sys.exit(main())
