# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..core import Package
from ..utils import get_local_config_file


@click.group(name='hardware')
def hardware_cli():
    ''' Supported hardware related commands '''


@hardware_cli.command(name='add')
@click.argument('hardware')
@click.option('--revision', '-r', multiple=True,
              help=('If present, specifies a revision to be '
                    'added within the given hardware. '
                    'This option can be repeated many times.'))
def add_supported_hardware_command(hardware, revision):
    ''' Add a supported hardware for the current package. '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        if hardware not in package.supported_hardware:
            package.add_supported_hardware(hardware)
        for rev in revision:
            package.add_supported_hardware_revision(hardware, rev)
        package.dump(pkg_file)
    except FileNotFoundError:
        print('ERROR: Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)


@hardware_cli.command(name='remove')
@click.argument('hardware')
@click.option('--revision', '-r', multiple=True,
              help=('If present, specifies a revision to be '
                    'removed from the given hardware. '
                    'This option can be repeated many times.'))
def remove_supported_hardware_command(hardware, revision):
    ''' Remove a supported hardware for the current package. '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        if not revision:
            package.remove_supported_hardware(hardware)
        else:
            for rev in revision:
                package.remove_supported_hardware_revision(hardware, rev)
        package.dump(pkg_file)
    except FileNotFoundError:
        print('ERROR: Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    except ValueError as err:
        print('ERROR: {}'.format(err))
        sys.exit(2)
