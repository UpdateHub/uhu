# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..package import Package
from ..package.exceptions import InvalidFileError, InvalidPackageFileError

from .push import Push


@click.command(name='push')
def push_command():
    """
    Makes a push transaction based on a package file.
    Package file must be in json format.
    """
    try:
        package = Package()
        sys.exit(Push(package).run())
    except InvalidFileError:
        raise click.BadParameter('Invalid file within package')
    except InvalidPackageFileError:
        raise click.BadParameter('Invalid package file')
