# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..core import Package
from ..core.parser import add_command, remove_command
from ..utils import get_local_config_file

from .pull import pull_command
from .push import push_command, status_command


@click.group(name='package')
def package_cli():
    ''' Package related commands '''


@package_cli.command('show')
def show_command():
    ''' Shows all configured images '''
    try:
        pkg_file = get_local_config_file()
        print(Package.from_file(pkg_file))
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)


@package_cli.command('export')
@click.argument('filename', type=click.Path(dir_okay=False))
def export_command(filename):
    ''' Copy package file to the given filename '''
    try:
        pkg_file = get_local_config_file()
        Package.from_file(pkg_file).dump(filename)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)


# Image commands
package_cli.add_command(add_command)
package_cli.add_command(remove_command)

# Transaction commands
package_cli.add_command(pull_command)
package_cli.add_command(push_command)
package_cli.add_command(status_command)
