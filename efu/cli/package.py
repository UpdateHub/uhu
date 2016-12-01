# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click
import requests

from ..core.options import MODES
from ..core.package import ACTIVE_INACTIVE_MODES
from ..exceptions import UploadError

from ._object import ClickOptionsParser, CLICK_OPTIONS
from ._push import PushCallback
from .utils import error, open_package


def _get_installation_set(pkg, set_):
    # This function must be removed when installation set gets symmetric
    if pkg.objects.is_single() and set_ is None:
        return 0
    return set_


@click.group(name='package')
def package_cli():
    ''' Package related commands '''


@package_cli.command('version')
@click.argument('version')
def set_version_command(version):
    ''' Sets package version '''
    with open_package() as package:
        package.version = version


@package_cli.command('show')
def show_command():
    ''' Shows all configured objects '''
    with open_package(read_only=True) as package:
        print(package)


@package_cli.command('export')
@click.argument('filename', type=click.Path(dir_okay=False))
def export_command(filename):
    ''' Copy package file to the given filename '''
    with open_package() as package:
        package.dump(filename)


@package_cli.command('active-inactive-backend')
@click.argument('backend', type=click.Choice(ACTIVE_INACTIVE_MODES))
def set_active_inactive_backend(backend):
    ''' Sets active-inactive backend '''
    with open_package() as package:
        package.active_inactive_backend = backend


# Object commands

@package_cli.command('add')
@click.argument('filename', type=click.Path(exists=True))
@click.option('--mode', '-m', type=click.Choice(sorted(MODES)),
              help='How the object will be installed', required=True)
@click.option('--installation-set', type=click.INT,
              help='The installation set to add object')
def add_object_command(filename, mode, installation_set, **options):
    ''' Adds an entry in the package file for the given artifact '''
    with open_package() as package:
        parser = ClickOptionsParser(mode, options)
        try:
            options = parser.clean()
        except ValueError as err:
            error(2, err)
        installation_set = _get_installation_set(package, installation_set)
        try:
            package.objects.create(
                filename, mode, options, index=installation_set)
        except ValueError as err:
            error(3, err)
        except TypeError as err:
            error(4, err)


# Adds all object options
for option in CLICK_OPTIONS.values():
    add_object_command.params.append(option)


@package_cli.command(name='edit')
@click.argument('object-id', type=click.INT)
@click.argument('key')
@click.argument('value')
@click.option('--installation-set', type=click.INT,
              help='The installation set to add object')
def edit_object_command(object_id, key, value, installation_set):
    ''' Edits an object property within package '''
    with open_package() as package:
        installation_set = _get_installation_set(package, installation_set)
        try:
            package.objects.update(
                object_id, key, value, index=installation_set)
        except ValueError as err:
            error(2, err)


@package_cli.command('remove')
@click.argument('object-id', type=click.INT)
@click.option('--installation-set', type=click.INT,
              help='The installation set to add object')
def remove_object_command(object_id, installation_set):
    ''' Removes the filename entry within package file '''
    with open_package() as package:
        installation_set = _get_installation_set(package, installation_set)
        package.objects.remove(object_id, index=installation_set)


# Transaction commands

@package_cli.command(name='push')
def push_command():
    ''' Pushes a package file to server with the given version. '''
    with open_package(read_only=True) as package:
        callback = PushCallback()
        package.load(callback)
        try:
            package.push(callback)
        except UploadError as err:
            error(2, err)
        except requests.exceptions.ConnectionError:
            error(3, 'Can\'t reach server')


@package_cli.command(name='pull')
@click.argument('package-uid')
@click.option('--full/--metadata', required=True,
              help='if pull should include all files or only the metadata.')
def pull_command(package_uid, full):
    ''' Downloads a package from server. '''
    with open_package() as package:
        package.uid = package_uid
        if not package.product:
            error(2, 'Product not set')
        if len(package.objects.all()) != 0:
            error(3, ('ERROR: You have a local package that '
                      'would be overwritten by this action.'))
        try:
            package.pull(full=full)
        except ValueError as err:
            error(4, err)
        except FileExistsError as err:
            error(5, err)


@package_cli.command(name='status')
@click.argument('package-uid')
def status_command(package_uid):
    ''' Prints the status of the given package '''
    with open_package(read_only=True) as package:
        package.uid = package_uid
        try:
            print(package.get_status())
        except ValueError as err:
            error(2, err)
