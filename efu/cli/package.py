# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..core import Package
from ..utils import get_local_config_file

from ._object import ObjectOptions, MODES
from .pull import pull_command
from .push import push_command


@click.group(name='package')
def package_cli():
    ''' Package related commands '''


@package_cli.command('new')
@click.argument('version')
def new_version_command(version):
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        package.version = version
        package.dump(pkg_file, full=True)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)


@package_cli.command('show')
def show_command():
    ''' Shows all configured objects '''
    try:
        pkg_file = get_local_config_file()
        print(Package.from_file(pkg_file))
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)


@package_cli.command('remove')
@click.argument('filename')
def remove_object_command(filename):
    ''' Removes the filename entry within package file '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        package.remove_object(filename)
        package.dump(pkg_file)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command.')
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


@package_cli.command('add')
@click.argument('filename', type=click.Path(exists=True))
@click.option(
    '--mode', '-m', type=click.Choice(MODES),
    help='How the object will be installed', required=True)
def add_object_command(filename, mode, **options):
    ''' Adds an entry in the package file for the given artifact '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        metadata = ObjectOptions(filename, mode, options).as_metadata()
        package.add_object(filename, metadata)
        package.dump(pkg_file)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(2)


# Adds all object options
for option in ObjectOptions.click_options:
    add_object_command.params.append(option)


@package_cli.command(name='status')
@click.argument('package_id')
def status_command(package_id):
    '''
    Prints the status of the given package
    '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        status = Package.get_status(package.product, package_id)
        print(status)
    except FileNotFoundError:
        print('Package file does not exist')
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(2)


# Transaction commands
package_cli.add_command(pull_command)
package_cli.add_command(push_command)
