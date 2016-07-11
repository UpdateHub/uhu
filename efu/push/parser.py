# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from .push import Push
from .exceptions import InvalidFileError, InvalidPackageFileError


@click.command(name='push')
@click.argument('package_file', type=click.Path())
def push_command(package_file):
    """
    Makes a push transaction based on a package file.
    Package file must be in json format.
    """
    try:
        sys.exit(Push(package_file).run())
    except InvalidFileError:
        raise click.BadParameter('Invalid file within package')
    except InvalidPackageFileError:
        raise click.BadParameter('Invalid package file')
