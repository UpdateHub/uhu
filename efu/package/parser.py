# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

import click

from .exceptions import DotEfuExistsError
from .parser_options import ALL_PARAMS
from .parser_modes import interactive_mode, explicity_mode
from .utils import create_efu_file


def set_image(filename, params):
    '''Stub function, will be replaced with proper image evaluation code'''

    params['filename'] = filename
    params['install-mode'] = params['install_mode'].name
    del params['install_mode']

    image = json.dumps(params, indent=4, sort_keys=True)
    print(image)


@click.command('add')
@click.pass_context
def add_command(ctx, filename, **params):
    ''' Adds an entry in the package file for the given artifact '''
    install_mode = ctx.install_mode
    if install_mode is not None:
        image = explicity_mode(install_mode, params)
    else:
        image = interactive_mode(ctx)
    set_image(filename, image)

add_command.params = ALL_PARAMS


@click.command('use')
@click.argument('product_id')
@click.argument('version')
def use_command(product_id, version):
    try:
        create_efu_file(product_id, version)
    except DotEfuExistsError:
        raise click.ClickException('.efu already initiated')
