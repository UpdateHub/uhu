# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

from .cliparser import CLIParser


def main():
    CLIParser()
    return 0


if __name__ == '__main__':
    sys.exit(main())
