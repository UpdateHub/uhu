# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..package import Package
from ..package.exceptions import InvalidFileError, InvalidPackageFileError

from .push import Push


@click.command(name='push')
@click.argument('version')
def push_command(version):
    '''
    Pushes a package file to server with the given version.
    '''
    try:
        package = Package(version)
        sys.exit(Push(package).run())
    except InvalidFileError:
        raise click.BadParameter('Invalid file within package')
    except InvalidPackageFileError:
        raise click.BadParameter('Invalid package file')
