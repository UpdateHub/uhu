# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json

import click

from pkgschema import validate_metadata, ValidationError

from ..core.object import Modes
from ..updatehub.api import get_package_status, UpdateHubError
from ..core.utils import dump_package, dump_package_archive
from ..ui import get_callback, show_cursor

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
        dump_package(package.to_template(with_version=False), filename)


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
    options['mode'] = mode
    with open_package() as package:
        try:
            package.objects.create(options)
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
                index, option, value, set_index=installation_set)
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
    callback = get_callback()
    with open_package(read_only=True) as package:
        try:
            package.push(callback)
        except UpdateHubError as err:
            error(2, err)
        finally:
            show_cursor()


@package_cli.command(name='status')
@click.argument('package-uid')
def status_command(package_uid):
    """Prints the status of the given package."""
    try:
        print(get_package_status(package_uid))
    except UpdateHubError as err:
        error(2, err)


@package_cli.command(name='metadata')
def metadata_command():
    """Loads package and prints its metadata."""
    with open_package(read_only=True) as package:
        metadata = package.to_metadata()
        print(json.dumps(metadata, indent=4, sort_keys=True))
    try:
        validate_metadata(metadata)
        print('Valid metadata.')
    except ValidationError as err:
        error(1, err)


@package_cli.command(name='archive')
@click.option('--output', type=click.Path(dir_okay=False),
              help="Where to write archive")
@click.option('--force', is_flag=True,
              help="Overwrites output file if output exists")
def archive_command(output, force):
    """Saves package as archive."""
    with open_package(read_only=True) as package:
        try:
            dump_package_archive(package, output, force)
        except FileExistsError as err:
            error(1, err)
        except ValueError as err:
            error(2, err)
