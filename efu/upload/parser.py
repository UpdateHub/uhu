# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

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
        transaction = Transaction(package_file)
        transaction.run()
    except InvalidFileError:
        click.echo('Invalid file within package')
        raise click.BadParameter
    except InvalidPackageFileError:
        click.echo('Invalid package file')
        raise click.BadParameter
