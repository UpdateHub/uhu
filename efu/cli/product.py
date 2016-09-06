# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from ..core.product import Product


@click.group(name='product')
def product_cli():
    ''' Product related commands '''
    pass


@product_cli.command()
@click.argument('uid')
def use_command(uid):
    ''' Sets the product '''
    print('here')
    try:
        Product.use(uid)
    except FileExistsError as err:
        raise click.ClickException(err)
