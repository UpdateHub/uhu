# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from .config.parser import config_command
from .package.parser import (
    use_command, export_command, cleanup_command,
    add_command, remove_command, show_command
)
from .pull.parser import pull_command
from .push.parser import push_command


@click.group()
def cli():
    ''' EasyFOTA utility '''
    pass


# Config commands
cli.add_command(config_command)

# Package commands
cli.add_command(use_command)
cli.add_command(export_command)
cli.add_command(cleanup_command)

# Image commands
cli.add_command(add_command)
cli.add_command(remove_command)
cli.add_command(show_command)

# Commit commands
cli.add_command(pull_command)
cli.add_command(push_command)
