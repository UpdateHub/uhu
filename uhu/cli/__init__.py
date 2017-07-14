# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import click

from .. import get_version
from ..repl import repl

from .config import config_cli, cleanup_command
from .hardware import hardware_cli
from .package import package_cli
from .product import product_cli


@click.group(invoke_without_command=True)
@click.option('--package', type=click.Path())
@click.version_option(
    get_version(), message='UpdateHub Utils - %(version)s')
@click.pass_context
def cli(ctx, package):
    """UpdateHub utility.

    To push packages, set USE_SERVER_URL environment variable to
    UpdateHub API server address.
    """
    if ctx.invoked_subcommand is None:
        repl(package)


# General commands
cli.add_command(cleanup_command)

# Subcommands
cli.add_command(config_cli)
cli.add_command(hardware_cli)
cli.add_command(package_cli)
cli.add_command(product_cli)
