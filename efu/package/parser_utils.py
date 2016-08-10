# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from copy import deepcopy

import click


NONE_DEFAULT = ''


def image_prompt(text, suffix, show_default=False, default=None):
    '''
    The same used in click, but with a better prompt for non required
    options
    '''
    prompt = text
    if default is not None and show_default:
        if default == NONE_DEFAULT:
            default = 'None'
        prompt = '%s [%s]' % (prompt, default)
    return prompt + suffix
click.termui._build_prompt = image_prompt  # pylint: disable=W0212


def get_param_names(params):
    return {param.name for param in params}


def replace_format(image):
    ''' adds ? into format property '''
    image = deepcopy(image)
    if image.get('format') is not None:
        image['format?'] = image.pop('format')
    return image


def replace_underscores(image):
    ''' cleans click _/- mess '''
    image = deepcopy(image)
    for key in tuple(image.keys()):
        option = key.replace('_', '-')
        image[option] = image.pop(key)
    return image


def replace_install_mode(image):
    ''' replace the object by name '''
    image = deepcopy(image)
    if not isinstance(image['install-mode'], str):
        image['install-mode'] = image['install-mode'].name
    return image


class InstallMode:

    def __init__(self, name, optional=None, required=None):
        optional = optional if optional else []
        required = required if required else []

        self.name = name
        self.params = required + optional
        self.required = required

        self._params_names = get_param_names(self.params)
        self._required_names = get_param_names(self.required)

    def is_valid(self, param):
        return param.name in self._params_names

    def is_required(self, param):
        return param.name in self._required_names


class InstallModeChoiceType(click.Choice):

    def __init__(self, modes):
        self.modes = modes
        super().__init__(self.modes.keys())

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        mode = self.modes.get(value)
        return mode


class LazyPromptOption(click.Option):
    '''
    An enhanced click Option class that nevers prompt at parsing time
    and supports and supports lazy evaluation.
    '''

    def __init__(self, *args, **kw):
        self.default_lazy = kw.pop('default_lazy', None)
        self.callback_lazy = kw.pop('callback_lazy', lambda x: (True, None))
        kw['prompt'], kw['default'] = None, None
        super().__init__(*args, **kw)
        self.prompt = self.name.replace('_', ' ').capitalize()

    def full_process_value(self, ctx, value):
        return click.Parameter.full_process_value(self, ctx, value)

    def prompt_for_value(self, ctx):
        default = self.default_lazy
        if self.is_bool_flag:
            return click.confirm(self.prompt, default)
        return click.prompt(self.prompt, default=default,
                            hide_input=self.hide_input,
                            confirmation_prompt=self.confirmation_prompt,
                            value_proc=lambda x: self.process_value(ctx, x))


class ImageOption(LazyPromptOption):
    '''
    Adds dependency support and a better prompt text for non required
    options.
    '''

    def __init__(self, *args, **kw):
        dependencies = kw.pop('dependencies', [])
        self.dependencies = {param.name for param in dependencies}
        super().__init__(*args, **kw)
        self.callback = self.validate

    @staticmethod
    def validate(ctx, param, value):
        ''' A callback to be called during parsing time '''
        # a present value implies non interactive mode
        if value is not None:
            # missing install-mode option in non interactive mode
            if ctx.install_mode is None:
                raise click.MissingParameter(
                    'You need to provide a install mode')
            # invalid param in currnet install mode
            if not ctx.install_mode.is_valid(param):
                raise click.UsageError(
                    '{} is not valid for {} install mode'.format(
                        param.name, ctx.install_mode.name))
        elif ctx.install_mode and ctx.install_mode.is_required(param):
            raise click.MissingParameter(ctx=ctx, param=param)
        return value

    def prompt_for_value(self, ctx):
        mode = ctx.install_mode
        if self.default_lazy is None and not mode.is_required(self):
            self.default_lazy = NONE_DEFAULT
        return super().prompt_for_value(ctx)
