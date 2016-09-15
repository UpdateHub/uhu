# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

import click

from ..utils import get_local_config_file

from .parser_options import ALL_PARAMS
from .parser_modes import interactive_mode, explicit_mode
from .parser_utils import (
    replace_format, replace_install_mode, replace_underscores)
from .utils import add_image


@click.command('add')
@click.pass_context
def add_command(ctx, filename, **params):
    ''' Adds an entry in the package file for the given artifact '''
    if not os.path.exists(get_local_config_file()):
        raise click.ClickException(
            'Package file does not exist. Create one with <efu use> command')
    install_mode = ctx.install_mode
    if install_mode is not None:
        image = explicit_mode(install_mode, params)
    else:
        image = interactive_mode(ctx)

    image = replace_format(image)
    image = replace_underscores(image)
    image = replace_install_mode(image)
    # finally, adds the image into package
    add_image(filename, image)

add_command.params = ALL_PARAMS
