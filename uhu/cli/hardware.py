# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import click

from .utils import error, open_package


@click.group(name='hardware')
def hardware_cli():
    """Supported hardware related commands."""


@hardware_cli.command(name='add')
@click.argument('hardware')
def add_supported_hardware(hardware):
    """Adds a hardware identifier to supported hardware list."""
    with open_package() as package:
        package.supported_hardware.add(hardware)


@hardware_cli.command(name='remove')
@click.argument('hardware')
def remove_supported_hardware(hardware):
    """Removes a hardware identifier from supported hardware list."""
    with open_package() as package:
        try:
            package.supported_hardware.remove(hardware)
        except KeyError as err:
            error(2, err)


@hardware_cli.command(name='reset')
def reset_supported_hardware_list():
    """Removes all supported hardware identifiers."""
    with open_package() as package:
        package.supported_hardware.reset()
