# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import sys
from contextlib import contextmanager

from ..core.package import Package
from ..core.utils import dump_package, load_package
from ..utils import get_local_config_file
from ..ui import show_cursor


@contextmanager
def open_package(read_only=False):
    """Context manager for package operations.

    It opens a package, gives control to the user and, finally, dumps
    the package. If read_only, it does not dump the package.
    """
    pkg_file = get_local_config_file()
    try:
        package = load_package(pkg_file)
    except FileNotFoundError:
        package = Package()
    except ValueError as err:
        print('Invalid configuration file: {}'.format(err))
        sys.exit(1)
    yield package
    if not read_only:
        dump_package(package.to_template(), pkg_file)


def error(code, msg):
    """Terminates cli with an error code and message for the user."""
    print('Error: {}'.format(msg))
    show_cursor()
    sys.exit(code)
