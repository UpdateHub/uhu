# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import re
from collections import OrderedDict
from copy import deepcopy


ASYMMETRIC_OPTIONS = ['target-device', 'target-path', 'volume']

INSTALL_CONDITION_BACKENDS = ['linux-kernel', 'u-boot']


class Option:
    """A wrapper over each option within options.json."""

    def __init__(self, conf):
        self.verbose_name = conf.get('verbose-name')
        self.metadata = conf.get('metadata')
        self.cli = conf.get('cli')
        self.help = conf.get('help')

        self.type = conf.get('type')
        self.is_volatile = conf.get('is_volatile', False)

        self.default = conf.get('default')
        self.min = conf.get('min')
        self.max = conf.get('max')
        self.choices = conf.get('choices')

        self.modes = tuple(conf.get('modes', []))
        self.required_in = tuple(conf.get('required_in', []))
        self.requirements = conf.get('requirements', {})

    def validate_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ['yes', 'y']:
                return True
            if value in ['no', 'n']:
                return False
        raise ValueError('Only y, yes, n and no values are allowed')

    def validate_int(self, value):
        if type(value) not in [int, str]:
            raise ValueError('Only integers are allowed')
        try:
            value = int(value)
        except ValueError:
            raise ValueError('Only integers are allowed')
        if self.min is not None and value < self.min:
            err = '{} is lesser than {}'
            raise ValueError(err.format(value, self.min))
        if self.max is not None and value > self.max:
            err = '{} is greater than {}'
            raise ValueError(err.format(value, self.max))
        return value

    def validate_path(self, value):
        """Validates if value is an absolute path."""
        value = str(value)
        result = re.match(r'^/[^\0]*', value)
        if result is None:
            err = '"{}" is not a valid absolut path'
            raise ValueError(err.format(value))
        return value

    def validate_str(self, value):
        value = str(value)
        if self.choices is not None:
            if value not in self.choices:
                err = '"{}" is not in {}'
                raise ValueError(err.format(value, self.choices))
        return value

    def validate_is_allowed(self, mode, value):
        """Checks if option is valid within mode."""
        if value is not None:
            if (mode not in self.modes) and (not self.is_volatile):
                err = 'Option "{}" is not valid in mode "{}".'
                raise ValueError(err.format(self, mode))

    def validate_is_required(self, mode, value):
        """Checks if option is required within mode."""
        if value is None and self.is_required(mode):
            err = 'Option "{}" is required for mode "{}".'
            raise ValueError(err.format(self, mode))

    def validate_requirements(self, values):
        """Checks if option requirements are satisfied."""
        for requirement, conf in self.requirements.items():
            if conf['type'] == 'value':
                if values.get(requirement) != conf['value']:
                    err = '"{}" must be equal to {} when using "{}" option.'
                    raise ValueError(err.format(
                        requirement, conf['value'], self.verbose_name))

    def is_required(self, mode):
        return mode in self.required_in

    def convert(self, value):
        """Convert the given value into object option value."""
        validator = self.VALIDATORS[self.type]
        return validator(self, value)

    VALIDATORS = {
        'str': validate_str,
        'bool': validate_bool,
        'int': validate_int,
        'path': validate_path,
    }

    def __str__(self):
        return str(self.verbose_name)


def load_options(fn):
    """Loads all options and modes from a given conf file."""
    options = OrderedDict()
    with open(fn) as fp:
        data = json.load(fp, object_pairs_hook=OrderedDict)
        for opt in data:
            options[opt['metadata']] = Option(opt)
    return options


def load_modes(options):
    """Loads all modes based on the given options."""
    modes = {}
    for option in options.values():
        for mode in option.modes:
            modes[mode] = modes.get(mode, []) + [option]
    return modes


OPTIONS = load_options(os.path.join(os.path.dirname(__file__), 'options.json'))
MODES = load_modes(OPTIONS)


class OptionsParser:
    """The base object option parser.

    It can handles if required options are present, if there are bad
    mode options present and can insert default values.
    """

    def __init__(self, mode, options):
        self.mode = mode
        self.options = MODES[self.mode]
        self.values = options

    def remove_null_values(self):
        """Removes all null values."""
        self.values = {
            option: value
            for option, value in self.values.items()
            if value is not None
        }

    def inject_default_values(self):
        """Add default option value for missing options."""
        for option in self.options:
            if option.metadata not in self.values:
                if option.default is not None:
                    # We must only inject possible options (eg. if an
                    # option with default value requires a non
                    # required option without default value, we MUST
                    # NOT insert this option).
                    if self._can_inject(option):
                        self.values[option.metadata] = option.default

    def _can_inject(self, option):
        """Method used during value injection step.

        It validates an option (which has a default value)
        requirements.

        It is necessary since we must only add default values if
        requirements are satisfied.
        """
        requirements = [req for req in self.options
                        if req.metadata in option.requirements]
        values = deepcopy(self.values)
        for req in requirements:
            if req.metadata not in self.values and option.default is not None:
                values[req.metadata] = req.default
            try:
                option.validate_requirements(values)
            except ValueError:
                return False
        return True

    def check_allowed_options(self):
        """Verifies if there are invalid options for the given mode."""
        for opt, value in self.values.items():
            option = OPTIONS[opt]
            option.validate_is_allowed(self.mode, value)

    def check_mode_requirements(self):
        """Verifies if there are missing options for the given mode."""
        for option in self.options:
            value = self.values.get(option.metadata)
            option.validate_is_required(self.mode, value)

    def check_options_requirements(self):
        """Verifies if all options requirements are satisfied."""
        for option in self.options:
            if self.values.get(option.metadata) is not None:
                option.validate_requirements(self.values)

    def convert_values(self):
        """Convert and validate values according to mode options."""
        for option in self.options:
            value = self.values.get(option.metadata)
            if value is not None:
                self.values[option.metadata] = option.convert(value)

    def clean(self):
        """Parse the given values according to the given mode.

        Returns a dict with the values normalized and cleaned.

        Raises ValueError in case something is wrong.
        """
        # First, we remove all nullable values
        self.remove_null_values()
        # With all trash removed,  we need to inject the default values
        self.inject_default_values()
        # Then, we check if there are invalid options for the given mode
        self.check_allowed_options()
        # We then check if there are missing required mode options
        self.check_mode_requirements()
        # Now we convert the values (ex. 'yes' -> True)
        self.convert_values()
        # Finally, we check if options requirements are satisfied
        self.check_options_requirements()
        return self.values
