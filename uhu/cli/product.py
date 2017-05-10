# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import click

from .utils import open_package


@click.group(name='product')
def product_cli():
    """Product related commands."""


@product_cli.command(name='use')
@click.argument('uid')
def use_command(uid):
    """Sets the product."""
    with open_package() as package:
        package.product = uid
