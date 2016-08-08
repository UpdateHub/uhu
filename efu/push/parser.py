# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..package import Package
from ..package.exceptions import (
    InvalidFileError, InvalidPackageFileError, PackageFileDoesNotExistError)

from .exceptions import CommitDoesNotExist
from .push import Push
from .utils import get_commit_status


@click.command(name='push')
@click.argument('version')
def push_command(version):
    '''
    Pushes a package file to server with the given version.
    '''
    try:
        package = Package(version)
        sys.exit(Push(package).run())
    except InvalidFileError:
        raise click.BadParameter('Invalid file within package')
    except InvalidPackageFileError:
        raise click.BadParameter('Invalid package file')


@click.command(name='status')
@click.argument('commit_id')
def status_command(commit_id):
    '''
    Prints the status of the given commit
    '''
    try:
        print(get_commit_status(commit_id))
    except PackageFileDoesNotExistError:
        print('Package file does not exist')
        sys.exit(1)
    except CommitDoesNotExist:
        print('Commit {} does not exist'.format(commit_id))
        sys.exit(2)
