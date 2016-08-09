# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click

from .pull import Pull
from ..package.exceptions import (
    PackageFileDoesNotExistError, PackageFileExistsError)
from ..push.exceptions import CommitDoesNotExist


@click.command(name='pull')
@click.argument('commit_id')
@click.option('--full/--metadata', required=True,
              help='if pull should include all files or only the metadata.')
def pull_command(commit_id, full):
    '''
    Pulls a commit from server.
    If --full is passed, all files and the package file will be downloaded.
    If --metadata is passed, only the package file will be downloaded.
    '''
    try:
        Pull(commit_id).pull(full)
    except PackageFileDoesNotExistError:
        print('Aborted!')
        print('Package file does not exist. Create one with <efu use> command')
        sys.exit(1)
    except CommitDoesNotExist:
        print('Aborted!')
        print('Commit {} does not exist'.format(commit_id))
        sys.exit(2)
    except PackageFileExistsError:
        print('Aborted!')
        print('You have a local package that '
              'would be overwritten by this action.')
        print('If you want to proceed, run <efu cleanup> and <efu use>.')
        sys.exit(3)
    except FileExistsError:
        print('Aborted!')
        print('You have local files that would be overwritten by this action.')
        sys.exit(4)
