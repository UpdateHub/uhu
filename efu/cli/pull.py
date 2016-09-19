# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..utils import get_local_config
from ..transactions.pull import Pull


@click.command(name='pull')
@click.argument('package_id')
@click.option('--full/--metadata', required=True,
              help='if pull should include all files or only the metadata.')
def pull_command(package_id, full):
    '''
    Pulls a commit from server.
    If --full is passed, all files and the package file will be downloaded.
    If --metadata is passed, only the package file will be downloaded.
    '''
    try:
        pkg = get_local_config()
        product = pkg['product']
    except FileNotFoundError:
        print('ERROR: Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    except KeyError:
        print('ERROR: Product not set')
        sys.exit(2)
    if len(pkg) > 1:
        print('ERROR: You have a local package that '
              'would be overwritten by this action.')
        sys.exit(3)
    try:
        Pull(product, package_id).pull(full=full)
    except ValueError as err:
        print(err)
        sys.exit(4)
    except FileExistsError as err:
        print(err)
        sys.exit(5)
