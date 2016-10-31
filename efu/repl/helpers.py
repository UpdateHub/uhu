# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter

from ..core.options import MODES


def check_arg(ctx, msg):
    ''' Checks if user has passed an argument '''
    if ctx.arg is None:
        raise ValueError(msg)


def check_version(ctx):
    ''' Checks if package already has a version '''
    if ctx.package.version is None:
        raise ValueError('You need to set a version first')


def check_product(ctx):
    ''' Checks if product is already set '''
    if ctx.package.product is None:
        raise ValueError('You need to set a product first')


def prompt_object_filename():
    ''' Prompts user for a valid filename '''
    msg = 'Choose a file to add into your package: '
    fn = prompt(msg, completer=PathCompleter()).strip()
    if not fn:
        raise ValueError('You must specify a file.')
    if not os.path.exists(fn):
        raise ValueError('"{}" does not exist.'.format(fn))
    if os.path.isdir(fn):
        raise ValueError('Only files are allowed.')
    return fn


def prompt_object_mode():
    ''' Prompts user for a object mode '''
    mode = prompt(
        'Choose a mode: ', completer=WordCompleter(sorted(MODES)))
    if not mode:
        raise ValueError('You must specify a mode.')
    if mode not in MODES:
        raise ValueError('You must specify a valid mode.')
    return mode


def prompt_object_options(mode):
    ''' Prompts user for object options '''
    print()
    print('Options')
    print('-------')
    options = {}
    for option in MODES[mode]:
        try:
            option.validate_requirements(options)
        except ValueError:
            break  # requirements not satisfied, skip this option
        if option.default is not None:
            default = option.default
            if option.type == 'bool':
                if default:
                    default = 'Y/n'
                else:
                    default = 'y/N'
            msg = '{} [{}]: '.format(option.verbose_name.title(), default)
        else:
            msg = '{}: '.format(option.verbose_name.title())
        if option.choices:
            completer = WordCompleter(option.choices)
        elif option.type == 'bool':
            completer = WordCompleter(['yes', 'no'])
        else:
            completer = WordCompleter([])
        value = prompt(msg, completer=completer).strip()
        value = value if value != '' else option.default
        cleaned_value = option.convert(value)
        options[option.metadata] = cleaned_value
    return options


def get_objects_completer(ctx):
    ''' Generates a prompt completer based on package objects. '''
    objects = enumerate(ctx.package.objects.all())
    return WordCompleter(['{}# {}'.format(index, obj.filename)
                          for index, obj in objects])


def parse_prompt_object_uid(value):
    ''' Parses value passed to a prompt using get_objects_completer '''
    try:
        return int(value.split('#')[0].strip())
    except ValueError:
        err = '"{}" is not a valid object UID.'
        raise ValueError(err.format(value))


def prompt_object_uid(ctx, msg):
    ''' Prompts user for an object UID '''
    completer = get_objects_completer(ctx)
    value = prompt(msg, completer=completer)
    return parse_prompt_object_uid(value)


def prompt_object_option(obj):
    ''' Prompts user for an object option '''
    mode = MODES[obj.mode]
    options = [option.metadata for option in mode]
    completer = WordCompleter(options)
    option = prompt('  Choose an option: ', completer=completer)
    if option not in options:
        raise ValueError('"{}" is not a valid option.'.format(option))
    return option


def prompt_object_option_value(option):
    ''' Prompts user for object option value '''
    # Option validation could be made here
    return prompt('  Set new value for "{}": '.format(option))


def prompt_package_uid():
    ''' Prompts user for a package UID '''
    # Package UID could be validated here
    uid = prompt('Type a package UID: ').strip()
    if not uid:
        raise ValueError('You need to specify a package UID')
    return uid


def prompt_pull():
    ''' Prompts user to set if a pull should download all files or not '''
    completer = WordCompleter(['yes', 'no'])
    full = prompt('Should we download all files? [Y/n]', completer=completer)
    full = full.strip().lower()
    if full in ['yes', 'y'] or full == '':
        full = True
    elif full in ['no', 'n']:
        full = False
    else:
        raise ValueError('Only yes or no values are allowed')
    return full
