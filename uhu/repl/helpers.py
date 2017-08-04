# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0
"""UHU REPL helper functions.

Includes reusable prompts, auto-completers, constraint checkers.
"""

import sys
from functools import partial, wraps

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.filters import HasCompletions
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys

from ..core.validators import validate_option_requirements
from ..core.object import Modes
from ..core._options import Options

from .completers import (
    ObjectFilenameCompleter, ObjectModeCompleter, ObjectOptionValueCompleter,
    ObjectUIDCompleter, YesNoCompleter)
from .exceptions import CancelPromptException
from .validators import (
    ObjectUIDValidator, ContainerValidator, ObjectOptionValueValidator,
    PackageUIDValidator)


manager = KeyBindingManager.for_prompt()  # pylint: disable=invalid-name


@manager.registry.add_binding(Keys.ControlD)
def ctrl_d(_):
    """Ctrl D quits appliaction returning 0 to sys."""
    sys.exit(0)


@manager.registry.add_binding(Keys.ControlC)
def ctrl_c(_):
    """Ctrl C raises an exception to be caught by functions.

    Main prompt must exit uhu with code status 1, while subprompts
    must returns to main prompt.
    """
    raise CancelPromptException('Cancelled operation.')


@manager.registry.add_binding(Keys.Enter, filter=HasCompletions())
def enter(event):
    """Enter selects a completion when has completions.

    When there is no completion available, submit value.
    """
    buffer = event.current_buffer
    state = buffer.complete_state
    if len(state.current_completions) == 1:
        state = state.go_to_index(0)
        buffer.apply_completion(state.current_completion)
    elif state.current_completion is None:
        buffer.complete_next()
    else:
        buffer.apply_completion(buffer.complete_state.current_completion)


def cancellable(func):
    """Decorator to cancell a current prompt."""
    @wraps(func)
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except CancelPromptException:
            pass  # Do nothing cancelling the current command
    return wrapper


# pylint: disable=invalid-name
prompt = partial(prompt, key_bindings_registry=manager.registry)


def check_arg(ctx, msg):
    """Checks if user has passed an argument.

    :param msg: The error message to display to the user in when an
                argument is not passed.
    """
    if ctx.arg is None:
        raise ValueError(msg)


def check_version(ctx):
    """Checks if package already has a version."""
    if ctx.package.version is None:
        raise ValueError('You need to set a version first')


def check_product(ctx):
    """Checks if product is already set."""
    if ctx.package.product is None:
        raise ValueError('You need to set a product first')


def set_product_prompt(product):
    """Sets prompt to be 'uhu [product]'."""
    return '[{}] uhu> '.format(product[:6])


def parse_prompt_object_uid(value):
    """Parses value passed to a prompt using get_objects_completer.

    :param value: A value returned by :func:`get_objects_completer`.
    """
    return int(value.split('#')[0].strip())


def prompt_object_options(n_sets, object_mode):
    """Prompts user for object options.

    :param n_sets: The number of installation sets in package.
    :param object_mode: A string indicating the object mode.
    """
    values = {}
    mode = Modes.get(object_mode)
    mode_options = [opt for opt in mode.options if not opt.volatile]
    for option in mode_options:
        try:
            validate_option_requirements(option, values)
        except ValueError:
            continue  # requirements not satisfied, skip this option
        if option.symmetric:
            value = prompt_object_option_value(option, object_mode)
        else:
            value = []
            for installation_set in range(n_sets):
                default = value[-1] if value else ''
                value.append(
                    prompt_object_option_value(
                        option=option,
                        mode=object_mode,
                        installation_set=installation_set,
                        default=default,
                    ))
            value = tuple(value)
        values[option] = value
    values = {opt.metadata: value for opt, value in values.items()}
    return values


def prompt_object_mode():
    """Prompts user for a object mode."""
    msg = 'Choose a mode: '
    completer = ObjectModeCompleter()
    validator = ContainerValidator('mode', Modes.names())
    mode = prompt(msg, completer=completer, validator=validator)
    return mode.strip()


def prompt_object_uid(package, installation_set=None):
    """Prompts user for an object UID.

    :param index: The object index within an object list.
    """
    if installation_set is None:
        installation_set = 0
    msg = 'Select an object: '
    completer = ObjectUIDCompleter(package, installation_set)
    validator = ObjectUIDValidator()
    value = prompt(msg, completer=completer, validator=validator)
    return parse_prompt_object_uid(value.strip())


def prompt_object_option(obj):
    """Prompts user for a valid option for the given object.

    :param obj: an uhu `Object` instance.
    """
    msg = 'Choose an option: '
    options = sorted(opt.metadata for opt in obj.options if not opt.volatile)
    completer = WordCompleter(options)
    validator = ContainerValidator('option', options)
    option = prompt(msg, completer=completer, validator=validator)
    return Options.get(option.strip())


def _get_object_option_value_message(option, set_=None):
    """Retuns a message for object_option_value prompt."""
    if option.default is not None:
        default_msg = option.default
        if option.type_name == 'boolean':
            if default_msg:
                default_msg = 'Y/n'
            else:
                default_msg = 'y/N'
        msg = '{} [{}]'.format(option.verbose_name.title(), default_msg)
    else:
        msg = '{}'.format(option.verbose_name.title())
    set_msg = ''
    if set_ is not None:
        set_msg = ' (installation set {})'.format(set_)
    msg = '{}{}: '.format(msg, set_msg)
    return msg


# pylint: disable=too-many-arguments
def _prompt_object_option_value(option, msg, completer, default, validator):
    """Retuns a value for object_option_value prompt."""
    value = prompt(
        msg, completer=completer, default=default, validator=validator).strip()
    if value == '':
        return option.default
    return option.validate(value)


def _get_object_option_value_completer(option, obj=None):
    """Retuns a completer for object_option_value prompt."""
    if option.choices:
        return ObjectOptionValueCompleter(option)
    elif option.type_name == 'boolean':
        return YesNoCompleter()
    elif option.metadata == 'filename':
        return ObjectFilenameCompleter()
    elif option.metadata == 'target-type':
        return WordCompleter(obj.target_types)


def prompt_object_option_value(
        option, mode, installation_set=None, default=''):
    """Given an object and an option, prompts user for a valid value.

    :param option: an uhu `Option` instance.
    :param mode: a valid Object mode string.
    :param installation_set: an int indicating the installation set.
    :param default: a default value to be displayed as placeholder.
    """
    mode = Modes.get(mode)
    msg = _get_object_option_value_message(option, installation_set)
    completer = _get_object_option_value_completer(option, mode)
    validator = ObjectOptionValueValidator(option, mode)
    value = _prompt_object_option_value(
        option, msg, completer, default, validator)
    return value


def prompt_package_uid():
    """Prompts user for a package UID."""
    msg = 'Type a package UID: '
    validator = PackageUIDValidator()
    uid = prompt(msg, validator=validator)
    return uid.strip()


def prompt_installation_set(package, msg=None):
    """Prompts user for a valid installation set.

    :param package: A core.package.Package instance.
    :param msg: The prompt message to display to user.
    :param all_sets: If True, allow to select an empty installation set.
    """
    if package.objects.is_single():
        return None

    objects = [(index, objs) for index, objs in enumerate(package.objects)]
    indexes = [str(i) for i, _ in objects]

    msg = msg if msg is not None else 'Select an installation set: '
    completer = WordCompleter(indexes)
    validator = ContainerValidator('installation set', indexes)
    installation_set = prompt(msg, completer=completer, validator=validator)
    return int(installation_set.strip())
