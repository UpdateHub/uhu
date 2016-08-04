# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from .parser_options import INSTALL_MODE
from .parser_utils import NONE_DEFAULT


def interactive_mode(ctx):
    ctx.install_mode = INSTALL_MODE.prompt_for_value(ctx)
    params = {'install_mode': ctx.install_mode}
    passed_params = set()
    for param in ctx.install_mode.params:
        callback_result, _ = param.callback_lazy(params)
        dependency_result = param.dependencies.issubset(passed_params)
        if callback_result and dependency_result:
            value = param.prompt_for_value(ctx)
            if value != NONE_DEFAULT:
                params[param.name] = value
                passed_params.add(param.name)
    return params


def explicit_mode(mode, params):
    cleaned_params = clean_params(params)
    final_params = inject_default_values(mode, cleaned_params)
    validate_dependencies(mode, final_params)
    return final_params


def clean_params(params):
    ''' Removes click garbage which obfuscate user passed params '''
    cleaned_params = {}
    for param, value in params.items():
        if value is not None:
            cleaned_params[param] = value
    return cleaned_params


def inject_default_values(mode, params):
    for param in mode.params:
        if param.name not in params.keys():
            if param.default_lazy is not None:
                params[param.name] = param.default_lazy
    return params


def validate_dependencies(mode, params):
    passed_params = set(params.keys())
    for param in mode.params:
        if param.name in passed_params:
            if not param.dependencies.issubset(passed_params):
                raise click.BadOptionUsage(
                    '{} option requires {}.'.format(
                        param.name, ', '.join(param.dependencies)))
            if param.callback_lazy is not None:
                result, msg = param.callback_lazy(params)
                if not result:
                    raise click.BadOptionUsage(msg)
