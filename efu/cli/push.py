# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from ..core import Package

from ..transactions.exceptions import CommitDoesNotExist
from ..transactions.push import Push
from ..transactions.utils import get_commit_status


@click.command(name='push')
@click.argument('version')
def push_command(version):
    '''
    Pushes a package file to server with the given version.
    '''
    package = Package(version)
    sys.exit(Push(package).run())


@click.command(name='status')
@click.argument('commit_id')
def status_command(commit_id):
    '''
    Prints the status of the given commit
    '''
    try:
        print(get_commit_status(commit_id))
    except FileNotFoundError:
        print('Package file does not exist')
        sys.exit(1)
    except CommitDoesNotExist:
        print('Commit {} does not exist'.format(commit_id))
        sys.exit(2)
