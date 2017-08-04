# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from copy import deepcopy

from ._options import OptionType, Options
from .install_condition import normalize_install_if_different


def normalize(obj, values):
    """Normalizes (clean and convert) all options.

    This is the first step of validation. We remove all options with
    None values. Then, we check if the remaning options are valid in
    this mode. Finally, we convert the value to what is expected on
    metadata.
    """
    cleaned = {}
    for option, value in values.items():
        option = Options.get(option)
        if value is not None:  # removes null values
            if option not in obj.options:  # checks allowed options
                err = '{} is a invalid option for {} mode'
                raise ValueError(err.format(option, obj.mode))
            cleaned[option] = option.validate(value)  # converts value
    return cleaned


def inject_default_values(obj, values):
    """Adds default values for all missing options."""
    for option in obj.options:
        values = inject_default_value(obj, option, values)
    return values


def inject_default_value(obj, option, values):
    """Adds the default value for a given option.

    The trickiest part in this process is that we cannot add
    values if its requirements are not satisfied. Since
    requirements may also have requirements and its requirements
    may also have default values, this problem is recursive.

    Some cases covered here:

    1. option is already presented: must do nothing

    2. option has no default: must do nothing

    3. option has default but no requirements: must insert
    default.

    4. option has default and requirements: must insert default
    and recursively insert requirements defaults.

    For all cases with injection, we must validate if the
    injection is possible (if the actual option requirements are
    satisfied). In case of invalid data, we must return the
    original values.
    """
    # We need a copy of the passed values since dicts are passed
    # by reference between function calls and we need be able to
    # return the original values in case of invalid data.
    original_values = deepcopy(values)

    # Option default value injection step
    if option not in values and option.default is not None:
        values[option] = option.default
    else:
        return original_values

    # Requirements default values injection step (recursive part)
    for req in option.requirements:
        values = inject_default_value(obj, req, values)

    # Validation step
    try:
        validate_option_requirements(option, values)
    except ValueError:
        return original_values
    return values


def validate_required_options(obj, values):
    """Checks if all mode required options are present."""
    for option in obj.required_options:
        if option not in values:
            err = 'Option "{}" is required for mode "{}".'
            raise ValueError(err.format(option, obj.mode))


def validate_options_requirements(values):
    """Verifies if all options requirements are satisfied."""
    for option in values:
        validate_option_requirements(option, values)


def validate_option_requirements(option, values):
    """Verifies if option requirements are satisfied."""
    # validate values argument
    for key in values.keys():
        if not isinstance(key, OptionType):
            err = 'values argument must have OptionType keys type (got {}).'
            raise TypeError(err.format(type(key)))

    if not option.requirements:
        return

    for req_option, req_value in option.requirements.items():
        if req_option not in values:
            err = ('You must specify a value for "{}" '
                   'when using "{}" options.')
            raise ValueError(err.format(req_option, option))
        value = values.get(req_option)
        if value != req_value:
            err = ('"{}" must be equal to "{}" when using "{}" '
                   'option. Got "{}".')
            raise ValueError(
                err.format(req_option, req_value, option, value))


def validate_options(obj, values):
    """Performs full object validation"""
    values = normalize_install_if_different(values)
    values = normalize(obj, values)
    values = inject_default_values(obj, values)
    validate_required_options(obj, values)
    validate_options_requirements(values)
    return values
