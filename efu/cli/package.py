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
        package.export(filename)


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
def add_object_command(filename, mode, **options):
    ''' Adds an entry in the package file for the given artifact '''
    with open_package() as package:
        parser = ClickOptionsParser(mode, options)
        try:
            options = parser.clean()
        except ValueError as err:
            error(2, err)
        try:
            package.objects.create(filename, mode, options)
        except ValueError as err:
            error(3, err)
        except TypeError as err:
            error(4, err)


# Adds all object options
for opt in CLICK_OPTIONS.values():
    add_object_command.params.append(opt)


@package_cli.command(name='edit')
@click.option('--index', type=click.INT, required=True,
              help='The object index')
@click.option('--installation-set', type=click.INT, required=True,
              help='The installation set to retrive object')
@click.option('--option', help='The object option to be edited', required=True)
@click.option('--value', help='The new value to be set', required=True)
def edit_object_command(index, installation_set, option, value):
    ''' Edits an object property within package '''
    with open_package() as package:
        try:
            package.objects.update(index, installation_set, option, value)
        except ValueError as err:
            error(2, err)


@package_cli.command('remove')
@click.argument('object-id', type=click.INT)
def remove_object_command(object_id):
    ''' Removes the filename entry within package file '''
    with open_package() as package:
        package.objects.remove(object_id)


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
