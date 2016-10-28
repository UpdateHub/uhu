# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter

from ..core import Package
from ..core.options import MODES


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


def set_product_uid(ctx):
    ''' Set product UID '''
    if ctx.arg is None:
        raise ValueError('You need to pass a product id')
    ctx.package.product = ctx.arg
    ctx.prompt = '[{}] efu> '.format(ctx.arg[:6])


def show_package(ctx):
    ''' Prints package content '''
    print(ctx.package)


def save_package(ctx):
    ''' Save a local package file based in current package '''
    if ctx.arg is None:
        raise ValueError('You need to pass a filename')
    ctx.package.dump(ctx.arg)


def cleanup(ctx):
    ''' Removes current package and set a new empty one '''
    ctx.package = Package()
    ctx.prompt = 'efu> '


def set_package_version(ctx):
    ''' Sets the current package version '''
    if ctx.arg is None:
        raise ValueError('You need to pass a version number')
    ctx.package.version = ctx.arg


def add_object(ctx):
    ''' Add an object into the current package '''
    # File
    fn = prompt(
        'Choose a file to add into your package: ',
        completer=PathCompleter()).strip()
    if not fn:
        raise ValueError('You must specify a file.')
    if not os.path.exists(fn):
        raise ValueError('"{}" does not exist.'.format(fn))
    if os.path.isdir(fn):
        raise ValueError('Only files are allowed.')

    # Mode
    mode = prompt(
        'Choose a mode: ', completer=WordCompleter(sorted(MODES)))
    if not mode:
        raise ValueError('You must specify a mode.')
    if mode not in MODES:
        raise ValueError('You must specify a valid mode.')

    # Options
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
    # FIX: Update to support active backup
    if len(ctx.package.objects) == 0:
        ctx.package.objects.add_list()
    ctx.package.objects.add(fn, mode, options)


def remove_object(ctx):
    ''' Removes an object from the current package '''
    completer = get_objects_completer(ctx)
    uid = prompt('  Choose a file to remove: ', completer=completer)
    if uid:
        uid = parse_prompt_object_uid(uid)
        # FIX: Update to support active backup
        ctx.package.objects.remove(uid)


def edit_object(ctx):
    ''' Edit an object within the current package '''
    completer = get_objects_completer(ctx)
    uid = prompt('  Choose a file to edit: ', completer=completer)
    if uid:
        uid = parse_prompt_object_uid(uid)
        # FIX: Update to support active backup
        obj = ctx.package.objects.get(uid)

    mode = MODES[obj.mode]
    options = [option.metadata for option in mode]
    completer = WordCompleter(options)
    option = prompt('  Choose an option: ', completer=completer)
    if option not in options:
        raise ValueError('"{}" is not a valid option.'.format(option))
    value = prompt('  Set new value for "{}": '.format(option))
    # FIX: Update to support active backup
    ctx.package.objects.update(uid, option, value)


def get_package_status(ctx):
    ''' Get the status from a package already pushed to server '''
    if ctx.package.product is None:
        raise ValueError('You need to set a product first')
    if ctx.arg is None:
        raise ValueError('You need to pass a package id')
    ctx.package.uid = ctx.arg
    print(ctx.package.get_status())


def push_package(ctx):
    ''' Uploade the current package to server '''
    if ctx.package.product is None:
        raise ValueError('You need to set a product first')
    if ctx.package.version is None:
        raise ValueError('You need to set a version first')
    from ..cli._push import PushCallback
    callback = PushCallback()
    ctx.package.load(callback)
    ctx.package.push(callback)


def pull_package(ctx):
    ''' Download and load a package from server '''
    if ctx.package.product is None:
        raise ValueError('You need to set a product first')
    # package uid
    uid = prompt('Type the package UID: ').strip()
    if not uid:
        raise ValueError('You need to specify a package UID')
    ctx.package.uid = uid

    # pull mode (full or only metadata)
    completer = WordCompleter(['yes', 'no'])
    full = prompt('Should we download all files? [Y/n]', completer=completer)
    full = full.strip().lower()
    if full in ['yes', 'y'] or full == '':
        full = True
    elif full in ['no', 'n']:
        full = False
    else:
        raise ValueError('Only yes or no values are allowed')
    ctx.package.pull(full)


def add_hardware(ctx):
    ''' Adds a supported hardware/revision into current package '''
    print('Specify the supported hardware for the current package.')
    print('You can pass many hardware as you want, separated by spaces.')
    hardwares = prompt('Hardwares: ').split()
    for hardware in hardwares:
        ctx.package.add_supported_hardware(hardware.strip())
        revisions = prompt('Specify a revision for {}: '.format(hardware))
        for rev in revisions.split():
            ctx.package.add_supported_hardware_revision(hardware, rev.strip())


def remove_hardware(ctx):
    ''' Removes a supported hardware/revision from current package '''
    print('Specify the supported hardware to be remove.')
    print('You can pass many hardware as you want, separated by spaces.')
    hardwares = prompt('Hardwares: ').split()
    print('For each hardware, specify the revisions to be removed, '
          'or left it blank to remove all revisions')
    for hardware in hardwares:
        revisions = prompt('Hardware {}: '.format(hardware)).strip()
        if not revisions:
            ctx.package.remove_supported_hardware(hardware)
            continue
        for revision in revisions.split():
            ctx.package.remove_supported_hardware_revision(
                hardware, revision.strip())
