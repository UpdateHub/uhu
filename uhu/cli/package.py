# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import json
import os

import click
import requests

from pkgschema import validate_metadata, ValidationError

from ..core.object import Modes
from ..core.package import Package
from ..exceptions import DownloadError, UploadError
from ..ui import get_callback
from ..utils import get_local_config_file

from ._object import CLICK_ADD_OPTIONS
from .utils import error, open_package


@click.group(name='package')
def package_cli():
    """Package related commands."""


@package_cli.command('version')
@click.argument('version')
def set_version_command(version):
    """Sets package version."""
    with open_package() as package:
        package.version = version


@package_cli.command('show')
def show_command():
    """Shows all configured objects."""
    with open_package(read_only=True) as package:
        print(package)


@package_cli.command('export')
@click.argument('filename', type=click.Path(dir_okay=False))
def export_command(filename):
    """Copy package file to the given filename."""
    with open_package() as package:
        package.export(filename)


# Object commands

@package_cli.command('add')
@click.argument('filename', type=click.Path(exists=True))
@click.option('--mode', '-m', type=click.Choice(Modes.names()),
              help='How the object will be installed', required=True)
def add_object_command(filename, mode, **options):
    """Adds an entry in the package file for the given artifact."""
    options = {CLICK_ADD_OPTIONS[opt].metadata: value
               for opt, value in options.items()
               if value is not None}
    options['filename'] = filename
    with open_package() as package:
        try:
            package.objects.create(mode, options)
        except ValueError as err:
            error(2, err)


# Adds all object options into cmd
for opt in CLICK_ADD_OPTIONS.values():
    add_object_command.params.append(opt)


@package_cli.command(name='edit')
@click.option('--index', type=click.INT, required=True,
              help='The object index')
@click.option('--installation-set', type=click.INT,
              help='The installation set to retrive object')
@click.option('--option', help='The object option to be edited', required=True)
@click.option('--value', help='The new value to be set', required=True)
def edit_object_command(index, installation_set, option, value):
    """Edits an object property within package."""
    with open_package() as package:
        try:
            package.objects.update(
                index, option, value, installation_set=installation_set)
        except ValueError as err:
            error(3, err)


@package_cli.command('remove')
@click.argument('object-id', type=click.INT)
def remove_object_command(object_id):
    """Removes the filename entry within package file."""
    with open_package() as package:
        package.objects.remove(object_id)


# Transaction commands

@package_cli.command(name='push')
def push_command():
    """Pushes a package file to server with the given version."""
    with open_package(read_only=True) as package:
        callback = get_callback()
        package.objects.load(callback)
        try:
            package.push(callback)
        except UploadError as err:
            error(2, err)
        except requests.exceptions.ConnectionError:
            error(3, 'Can\'t reach server')
        except ValidationError:
            error(4, 'Tempered configuration file (invalid metadata)')


@package_cli.command(name='pull')
@click.argument('package-uid')
@click.option('--metadata', is_flag=True,
              help='Downloads metadata.json too.')
@click.option('--objects', is_flag=True,
              help='Downloads all objects too.')
@click.option('--output', type=click.Path(
                  file_okay=False, writable=True, resolve_path=True),
              help='Output directory', default='.')
def pull_command(package_uid, metadata, objects, output):
    """Pulls a package from server."""
    if not os.path.exists(output):
        os.mkdir(output)
    os.chdir(output)

    pkg_file = get_local_config_file()
    if os.path.exists(pkg_file):
        error(1, 'You have a local configuration that would be overwritten.')

    try:
        pkg_metadata = Package.download_metadata(package_uid)
        package = Package.from_metadata(pkg_metadata)
        if objects:
            package.download_objects(package_uid)
        if metadata:
            with open('metadata.json', 'w') as fp:
                json.dump(pkg_metadata, fp, indent=4, sort_keys=True)
        package.dump(pkg_file)
    except DownloadError as err:
        error(2, err)


@package_cli.command(name='status')
@click.argument('package-uid')
def status_command(package_uid):
    """Prints the status of the given package."""
    with open_package(read_only=True) as package:
        package.uid = package_uid
        try:
            print(package.get_status())
        except ValueError as err:
            error(2, err)


@package_cli.command(name='metadata')
def metadata_command():
    """Loads package and prints its metadata."""
    with open_package(read_only=True) as package:
        package.objects.load()
        metadata = package.metadata()
        print(json.dumps(metadata, indent=4, sort_keys=True))
    try:
        validate_metadata(metadata)
        print('Valid metadata.')
    except ValidationError as err:
        error(1, err)
