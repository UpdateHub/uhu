# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from prompt_toolkit import prompt

from ..core import Package

from . import helpers


# Product

def set_product_uid(ctx):
    ''' Set product UID '''
    helpers.check_arg(ctx, 'You need to pass a product id')
    ctx.package.product = ctx.arg
    ctx.prompt = '[{}] efu> '.format(ctx.arg[:6])


# Package

def set_package_version(ctx):
    ''' Sets the current package version '''
    helpers.check_arg(ctx, 'You need to pass a version number')
    ctx.package.version = ctx.arg


def show_package(ctx):
    ''' Prints package content '''
    print(ctx.package)


def save_package(ctx):
    ''' Save a local package file based in current package '''
    helpers.check_arg(ctx, 'You need to pass a filename')
    ctx.package.dump(ctx.arg)


def clean_package(ctx):
    ''' Removes current package and set a new empty one '''
    ctx.package = Package()
    ctx.prompt = 'efu> '


# Objects

def add_object(ctx):
    ''' Add an object into the current package '''
    fn = helpers.prompt_object_filename()
    mode = helpers.prompt_object_mode()
    options = helpers.prompt_object_options(mode)
    # FIX: Update to support active backup
    if len(ctx.package.objects) == 0:
        ctx.package.objects.add_list()
    ctx.package.objects.add(fn, mode, options)


def remove_object(ctx):
    ''' Removes an object from the current package '''
    msg = '  Choose a file to remove: '
    uid = helpers.prompt_object_uid(ctx, msg)
    # FIX: Update to support active backup
    ctx.package.objects.remove(uid)


def edit_object(ctx):
    ''' Edit an object within the current package '''
    msg = '  Choose a file to edit: '
    uid = helpers.prompt_object_uid(ctx, msg)
    # FIX: Update to support active backup
    obj = ctx.package.objects.get(uid)
    option = helpers.prompt_object_option(obj)
    value = helpers.prompt_object_option_value(option)
    # FIX: Update to support active backup
    ctx.package.objects.update(uid, option, value)


# Transactions

def push_package(ctx):
    ''' Uploade the current package to server '''
    helpers.check_product(ctx)
    helpers.check_version(ctx)
    from ..cli._push import PushCallback
    callback = PushCallback()
    ctx.package.load(callback)
    ctx.package.push(callback)


def pull_package(ctx):
    ''' Download and load a package from server '''
    helpers.check_product(ctx)
    ctx.package.uid = helpers.prompt_package_uid()
    full = helpers.prompt_pull()
    ctx.package.pull(full)


def get_package_status(ctx):
    ''' Get the status from a package already pushed to server '''
    helpers.check_product(ctx)
    helpers.check_arg(ctx, 'You need to pass a package id')
    ctx.package.uid = ctx.arg
    print(ctx.package.get_status())


# Hardwares

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
