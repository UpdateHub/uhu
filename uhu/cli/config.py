# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import click

from ..config import config
from ..utils import remove_local_config
from .utils import error


@click.group(name='config')
def config_cli():
    """Configures uhu utility."""


@config_cli.command(name='init')
def init_command():
    """Sets uhu required initial configuration."""
    access = input('UpdateHub Access Key ID: ')
    secret = input('UpdateHub Systems Secret Access Key: ')
    config.set_credentials(access, secret)
    path = input('UpdateHub Private Key path: ')
    config.set_private_key_path(path)


@config_cli.command(name='set')
@click.argument('entry')
@click.argument('value')
@click.option('--section', help='Section to write the configuration')
def set_command(entry, value, section):
    """Sets the given VALUE in a configuration ENTRY."""
    config.set(entry, value, section=section)


@config_cli.command(name='get')
@click.argument('entry')
@click.option('--section', help='Section to write the configuration')
def get_command(entry, section):
    """Gets the value from a given ENTRY."""
    value = config.get(entry, section=section)
    if value:
        print(value)


@click.command('cleanup')
def cleanup_command():
    """Removes uhu local config file."""
    try:
        remove_local_config()
    except FileNotFoundError:
        error(1, 'Package file already deleted.')
