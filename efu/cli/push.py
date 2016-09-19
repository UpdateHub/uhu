# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..core import Package
from ..transactions.push import Push
from ..utils import get_local_config_file


@click.command(name='push')
@click.argument('version')
def push_command(version):
    '''
    Pushes a package file to server with the given version.
    '''
    pkg_file = get_local_config_file()
    package = Package.from_file(pkg_file)
    package.version = version
    sys.exit(Push(package).run())
