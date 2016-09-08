# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from ..core.parser import (
    export_command, cleanup_command, add_command, remove_command, show_command)
from .config import config_cli
from .product import product_cli
from .pull import pull_command
from .push import push_command, status_command


@click.group()
def cli():
    ''' EasyFOTA utility '''
    pass


# Config commands
cli.add_command(config_cli)

# Product commands
cli.add_command(product_cli)

# Package commands
cli.add_command(export_command)
cli.add_command(cleanup_command)

# Image commands
cli.add_command(add_command)
cli.add_command(remove_command)
cli.add_command(show_command)

# Commit commands
cli.add_command(pull_command)
cli.add_command(push_command)
cli.add_command(status_command)
