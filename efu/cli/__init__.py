# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from .. import get_efu_version
from ..repl import efu_interactive

from .config import config_cli, cleanup_command
from .hardware import hardware_cli
from .package import package_cli
from .product import product_cli


@click.group(invoke_without_command=True)
@click.option('--package', type=click.Path())
@click.version_option(
    get_efu_version(), message='EasyFOTA Utils - %(version)s')
@click.pass_context
def cli(ctx, package):
    ''' EasyFOTA utility '''
    if ctx.invoked_subcommand is None:
        efu_interactive(package)


# General commands
cli.add_command(cleanup_command)

# Subcommands
cli.add_command(config_cli)
cli.add_command(hardware_cli)
cli.add_command(package_cli)
cli.add_command(product_cli)
