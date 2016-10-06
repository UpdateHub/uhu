# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from ..core.options import OPTIONS, OptionsParser


TYPES = {
    'int': click.INT,
    'str': click.STRING,
    'bool': click.BOOL,
    'path': click.Path(readable=False),
}


class ClickObjectOption(click.Option):

    def __init__(self, option):
        if option.choices:
            type_ = click.Choice(option.choices)
        elif option.min or option.max:
            type_ = click.IntRange(min=option.min, max=option.max)
        else:
            type_ = TYPES[option.type]
        super().__init__(
            param_decls=option.cli, help=option.help,
            default=None, type=type_)
        self.default_lazy = option.default
        self.metadata = option.metadata


CLICK_OPTIONS = {}
for opt in OPTIONS.values():
    if not opt.is_volatile:
        click_option = ClickObjectOption(opt)
        CLICK_OPTIONS[click_option.name] = click_option


class ClickOptionsParser(OptionsParser):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.options = {CLICK_OPTIONS[opt].metadata: value
                        for opt, value in self.options.items()
                        if value is not None}

    def get_option_display(self, option):
        return option.cli[0]
