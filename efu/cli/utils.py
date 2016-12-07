# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys
from contextlib import contextmanager

from ..core import Package
from ..utils import get_local_config_file


@contextmanager
def open_package(read_only=False):
    """Context manager for package operations.

    It opens a package, gives control to the user and, finally, dumps
    the package. If read_only, it does not dump the package.
    """
    pkg_file = get_local_config_file()
    try:
        package = Package.from_file(pkg_file)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    except ValueError:
        print('Invalid configuration file.')
        sys.exit(1)
    yield package
    if not read_only:
        package.dump(pkg_file)


def error(code, msg):
    """Terminates cli with an error code and message for the user."""
    print('Error: {}'.format(msg))
    sys.exit(code)
