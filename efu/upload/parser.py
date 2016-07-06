# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from .upload import Transaction
from .exceptions import InvalidFileError, InvalidPackageFileError


@click.command(name='upload')
@click.argument('package_file', type=click.Path())
def transaction_command(package_file):
    """
    Makes a upload transaction based on a package file.
    Package file must be in json format.
    """
    try:
        sys.exit(Transaction(package_file).run())
    except InvalidFileError:
        raise click.BadParameter('Invalid file within package')
    except InvalidPackageFileError:
        raise click.BadParameter('Invalid package file')
