# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from .pull.parser import pull_command
from .push.parser import push_command
from .config.parser import config_command


@click.group()
def cli():
    ''' EasyFOTA utility '''
    pass


cli.add_command(pull_command)
cli.add_command(push_command)
cli.add_command(config_command)
