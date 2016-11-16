# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter

from ..core.options import MODES, Option, PACKAGE_MODE_BACKENDS
from ..utils import indent

from . import prompt


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


def set_product_prompt(product):
    ''' Sets prompt to be 'efu [product]' '''
    return '[{}] efu> '.format(product[:6])


def prompt_object_filename(msg=None, indent_level=0):
    ''' Prompts user for a valid filename '''
    msg = 'Choose a file to add into your package' if msg is None else msg
    msg = indent(msg, indent_level, all_lines=True)
    fn = prompt('{}: '.format(msg), completer=PathCompleter()).strip()
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
            continue  # requirements not satisfied, skip this option
        options[option.metadata] = prompt_object_option_value(option)
    return options


def get_objects_completer(ctx, index):
    ''' Generates a prompt completer based on package objects. '''
    objects = enumerate(ctx.package.objects.get_list(index))
    return WordCompleter(['{}# {}'.format(index, obj.filename)
                          for index, obj in objects])


def parse_prompt_object_uid(value):
    ''' Parses value passed to a prompt using get_objects_completer '''
    try:
        return int(value.split('#')[0].strip())
    except ValueError:
        err = '"{}" is not a valid object UID.'
        raise ValueError(err.format(value))


def prompt_object_uid(ctx, msg, index):
    ''' Prompts user for an object UID '''
    completer = get_objects_completer(ctx, index)
    value = prompt(msg, completer=completer)
    return parse_prompt_object_uid(value)


def prompt_object_option(obj):
    ''' Prompts user for an object option '''
    mode = MODES[obj.mode]
    options = {option.verbose_name: option for option in mode}

    # hack to let user update object filename
    options['filename'] = Option({'metadata': 'filename'})

    completer = WordCompleter(sorted(options))
    value = prompt('  Choose an option: ', completer=completer)
    option = options.get(value)
    if option is None:
        raise ValueError('"{}" is not a valid option.'.format(value))
    return option


def prompt_object_option_value(option, indent_level=0):
    ''' Prompts user for object option value '''
    if option.metadata == 'filename':
        return prompt_object_filename('Select a new file', indent_level=2)
    if option.default is not None:
        default = option.default
        if option.type == 'bool':
            if default:
                default = 'Y/n'
            else:
                default = 'y/N'
        msg = '{} [{}]'.format(option.verbose_name.title(), default)
    else:
        msg = '{}'.format(option.verbose_name.title())
    if option.choices:
        completer = WordCompleter(option.choices)
    elif option.type == 'bool':
        completer = WordCompleter(['yes', 'no'])
    else:
        completer = WordCompleter([])
    msg = indent(msg, indent_level, all_lines=True)
    value = prompt('{}: '.format(msg), completer=completer).strip()
    value = value if value != '' else option.default
    return option.convert(value)


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


def prompt_installation_set(ctx, msg=None, empty=True):
    '''
    Prompts user for a valid installation set.
    If not empty is True, only sets with objects are valid.
    '''
    if ctx.package.objects.is_single():
        return None
    objects = [(index, objs) for index, objs in enumerate(ctx.package.objects)]
    if not empty:
        objects = [(index, objs) for index, objs in objects if objs]
        if len(objects) == 0:
            raise ValueError('There is no object to operate.')
        if len(objects) == 1:
            index, _ = objects[0]
            return index
    msg = msg if msg is not None else 'Select an installation set: '
    indexes = [str(i) for i, _ in objects]
    completer = WordCompleter(indexes)
    index = prompt(msg, completer=completer).strip()
    try:
        if index not in indexes:
            raise ValueError
        index = int(index)
    except (ValueError, TypeError):
        raise ValueError('"{}" is not a valid installation set.'.format(index))
    return index


def prompt_package_mode():
    ''' Prompts for a valid package mode '''
    modes = ['single', 'active-backup']
    completer = WordCompleter(modes)
    mode = prompt(
        'Choose a package mode [single/active-backup]: ',
        completer=completer).strip().lower()
    if mode not in modes:
        raise ValueError('You need to specify a valid package mode.')
    return mode


def prompt_active_backup_backend():
    ''' Prompts for a valid active backup backend '''
    completer = WordCompleter(PACKAGE_MODE_BACKENDS)
    msg = 'Choose an active backup backend: '
    backend = prompt(msg, completer=completer).strip().lower()
    if backend not in PACKAGE_MODE_BACKENDS:
        raise ValueError('"{}" is not a valid backend.'.format(backend))
    return backend
