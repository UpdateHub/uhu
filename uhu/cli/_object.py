# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import click

from ..core._options import Options


TYPES = {
    'absolute_path': click.Path(readable=False),
    'boolean': click.BOOL,
    'integer': click.INT,
    'string': click.STRING,
}


class ClickObjectOption(click.Option):

    def __init__(self, option):
        if option.choices:
            type_ = click.Choice(option.choices)
        elif option.min is not None or option.max is not None:
            type_ = click.IntRange(min=option.min, max=option.max)
        else:
            type_ = TYPES[option.type_name]
        super().__init__(
            param_decls=option.cli, help=option.help,
            default=None, type=type_)
        self.metadata = option.metadata


def get_object_options():
    options = {}
    for option in Options.all():
        if not option.volatile and option != Options.get('filename'):
            click_option = ClickObjectOption(option)
            options[click_option.name] = click_option
    return options


CLICK_ADD_OPTIONS = get_object_options()
