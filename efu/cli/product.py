# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from ..core.product import Product


@click.group(name='product')
def product_cli():
    ''' Product related commands '''


@product_cli.command(name='use')
@click.argument('uid')
@click.option('--force', '-f', is_flag=True)
def use_command(uid, force):
    ''' Sets the product '''
    try:
        Product.use(uid, force=force)
    except FileExistsError as err:
        raise click.ClickException(err)
