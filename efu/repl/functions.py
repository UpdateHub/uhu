# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License
"""Main EFU REPL command functions."""

from ..config import config
from ..core.installation_set import InstallationSetMode
from ..core.package import Package

from . import helpers
from .helpers import prompt


# Config

@helpers.cancellable
def set_authentication():
    """Sets user access and secret keys."""
    access = prompt('EasyFOTA Access Key ID: ')
    secret = prompt('EasyFota Systems Secret Access Key: ')
    config.set_initial(access, secret)


# Product

def set_product_uid(ctx):
    """Set product UID."""
    helpers.check_arg(ctx, 'You need to pass a product id')
    ctx.package.product = ctx.arg
    ctx.prompt = helpers.set_product_prompt(ctx.arg)


# Package

def set_package_version(ctx):
    """Sets the current package version."""
    helpers.check_arg(ctx, 'You need to pass a version number')
    ctx.package.version = ctx.arg


def show_package(ctx):
    """Prints package content."""
    print(ctx.package)


def save_package(ctx):
    """Save a local package file based in current package."""
    helpers.check_arg(ctx, 'You need to pass a filename')
    ctx.package.dump(ctx.arg)


def clean_package(ctx):
    """Removes current package and set a new empty one."""
    ctx.package = Package(InstallationSetMode.ActiveInactive)
    ctx.prompt = 'efu> '


# Objects

@helpers.cancellable
def add_object(ctx):
    """Add an object into the current package."""
    filename = helpers.prompt_object_filename()
    mode = helpers.prompt_object_mode()
    options = helpers.prompt_object_options(mode)
    ctx.package.objects.create(filename, mode, options)


@helpers.cancellable
def remove_object(ctx):
    """Removes an object from the current package."""
    index = helpers.prompt_object_uid(ctx.package)
    ctx.package.objects.remove(index)


@helpers.cancellable
def edit_object(ctx):
    """Edit an object within the current package."""
    set_ = helpers.prompt_installation_set(ctx.package)
    index = helpers.prompt_object_uid(ctx.package, set_)
    obj = ctx.package.objects.get(index=index, installation_set=set_)
    option = helpers.prompt_object_option(obj)
    value = helpers.prompt_object_option_value(
        option, obj.mode, indent_level=2)
    ctx.package.objects.update(index, set_, option.metadata, value)


# Transactions

def push_package(ctx):
    """Uploade the current package to server."""
    helpers.check_product(ctx)
    helpers.check_version(ctx)
    from ..cli._push import PushCallback
    callback = PushCallback()
    ctx.package.load(callback)
    ctx.package.push(callback)


@helpers.cancellable
def pull_package(ctx):
    """Download and load a package from server."""
    helpers.check_product(ctx)
    ctx.package.uid = helpers.prompt_package_uid()
    full = helpers.prompt_pull()
    ctx.package.pull(full)


def get_package_status(ctx):
    """Get the status from a package already pushed to server."""
    helpers.check_product(ctx)
    helpers.check_arg(ctx, 'You need to pass a package id')
    ctx.package.uid = ctx.arg
    print(ctx.package.get_status())


# Hardwares

@helpers.cancellable
def add_hardware(ctx):
    """Adds a supported hardware/revision into current package."""
    print('Specify the supported hardware for the current package.')
    print('You can pass many hardware as you want, separated by spaces.')
    hardwares = prompt('Hardwares: ').split()
    for hardware in hardwares:
        ctx.package.add_supported_hardware(hardware.strip())
        revisions = prompt('Specify a revision for {}: '.format(hardware))
        for rev in revisions.split():
            ctx.package.add_supported_hardware_revision(hardware, rev.strip())


@helpers.cancellable
def remove_hardware(ctx):
    """Removes a supported hardware/revision from current package."""
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
