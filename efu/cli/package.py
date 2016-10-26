# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click
import requests

from ..core import Package
from ..core.options import MODES
from ..transactions.exceptions import (
    StartPushError, UploadError, FinishPushError)
from ..utils import get_local_config_file

from ._object import ClickOptionsParser, CLICK_OPTIONS
from ._push import PushCallback


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
        package.dump(pkg_file)
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
@click.argument('object-id', type=int)
def remove_object_command(object_id):
    ''' Removes the filename entry within package file '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        # FIX: Update to support active backup
        package.objects.remove(0, object_id)
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
    '--mode', '-m', type=click.Choice(sorted(MODES)),
    help='How the object will be installed', required=True)
def add_object_command(filename, mode, **options):
    ''' Adds an entry in the package file for the given artifact '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    parser = ClickOptionsParser(mode, options)
    try:
        options = parser.clean()
    except ValueError as err:
        print(err)
        sys.exit(2)
    # FIX: Update to support active backup
    if len(package.objects) == 0:
        package.objects.add_list()
    package.objects.add(0, filename, mode, options)
    package.dump(pkg_file)


# Adds all object options
for option in CLICK_OPTIONS.values():
    add_object_command.params.append(option)


@package_cli.command(name='edit')
@click.argument('object-id', type=int)
@click.argument('key')
@click.argument('value')
def edit_object_command(object_id, key, value):
    ''' Edits an object property within package '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        # FIX: Update to support active backup
        package.objects.update(0, object_id, key, value)
        package.dump(pkg_file)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(2)


@package_cli.command(name='status')
@click.argument('package-uid')
def status_command(package_uid):
    '''
    Prints the status of the given package
    '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        package.uid = package_uid
        print(package.get_status())
    except FileNotFoundError:
        print('Package file does not exist')
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(2)


# Transaction commands
@package_cli.command(name='push')
def push_command():
    '''
    Pushes a package file to server with the given version.
    '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
    except FileNotFoundError:
        print('Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    callback = PushCallback()
    package.load(callback)
    try:
        package.push(callback)
    except StartPushError as err:
        print(err)
        sys.exit(2)
    except UploadError as err:
        print(err)
        sys.exit(3)
    except FinishPushError as err:
        print(err)
        sys.exit(4)
    except requests.exceptions.ConnectionError:
        print("ERROR: Can't reach server")
        sys.exit(5)


@package_cli.command(name='pull')
@click.argument('package-uid')
@click.option('--full/--metadata', required=True,
              help='if pull should include all files or only the metadata.')
def pull_command(package_uid, full):
    '''
    Downloads a package from server.
    '''
    try:
        pkg_file = get_local_config_file()
        package = Package.from_file(pkg_file)
        package.uid = package_uid
    except FileNotFoundError:
        print('ERROR: Package file does not exist. '
              'Create one with <efu use> command')
        sys.exit(1)
    if not package.product:
        print('ERROR: Product not set')
        sys.exit(2)
    if len(package) != 0:
        print('ERROR: You have a local package that '
              'would be overwritten by this action.')
        sys.exit(3)
    try:
        package.pull(full=full)
    except ValueError as err:
        print(err)
        sys.exit(4)
    except FileExistsError as err:
        print(err)
        sys.exit(5)
