# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import sys

import click

from ..utils import get_package_file
from .exceptions import (
    PackageFileDoesNotExistError, PackageFileExistsError,
    ImageDoesNotExistError
)
from .parser_options import ALL_PARAMS
from .parser_modes import interactive_mode, explicit_mode
from .utils import (
    create_package_file, remove_package_file,
    add_image, remove_image
)


@click.command('use')
@click.argument('product_id')
@click.argument('version')
def use_command(product_id, version):
    ''' Creates a package file '''
    try:
        create_package_file(product_id, version)
    except PackageFileExistsError:
        raise click.ClickException('Package file already exists.')


@click.command('add')
@click.pass_context
def add_command(ctx, filename, **params):
    ''' Adds an entry in the package file for the given artifact '''
    if not os.path.exists(get_package_file()):
        raise click.ClickException(
            'Package file does not exist. Create one with <efu use> command')
    install_mode = ctx.install_mode
    if install_mode is not None:
        image = explicit_mode(install_mode, params)
    else:
        image = interactive_mode(ctx)
    add_image(filename, image)

add_command.params = ALL_PARAMS


@click.command('rm')
@click.argument('filename')
def remove_command(filename):
    ''' Removes the filename entry within package file '''
    try:
        remove_image(filename)
    except PackageFileDoesNotExistError:
        print('Package file does not exist. '
              'Create one with <efu use> command.')
        sys.exit(1)
    except ImageDoesNotExistError:
        print('{} does not exist within package.'.format(filename))
        sys.exit(2)


@click.command('cleanup')
def cleanup_command():
    ''' Removes all efu generated files '''
    try:
        remove_package_file()
    except PackageFileDoesNotExistError:
        print('Package file already deleted.')
        sys.exit(1)
