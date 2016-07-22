# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from .pull import Pull


@click.command(name='pull')
@click.argument('product')
@click.argument('commit')
def pull_command(product, commit):
    ''' Download a commit '''
    Pull(product, commit).pull()
