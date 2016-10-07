# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import re
from collections import OrderedDict


class Option:
    ''' A wrapper over each option within options.json '''

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
        ''' Validates if value is an absolute path '''
        value = str(value)
        result = re.match(r'^/[^\0]*', value)
        if result is None:
            err = '{} is not a valid absolut path'
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
        ''' Checks if option is valid within mode '''
        if value is not None:
            if (mode not in self.modes) and (not self.is_volatile):
                err = 'Option "{}" is not valid in mode "{}".'
                raise ValueError(err.format(self, mode))

    def validate_is_required(self, mode, value):
        ''' Checks if option is required within mode '''
        if value is None and mode in self.required_in:
            err = 'Option "{}" is required for mode "{}".'
            raise ValueError(err.format(self, mode))

    def validate(self, mode, value):
        ''' Full validation '''
        self.validate_is_required(mode, value)
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
    ''' Loads all options and modes from a given conf file '''
    options = OrderedDict()
    with open(fn) as fp:
        data = json.load(fp, object_pairs_hook=OrderedDict)
        for opt in data:
            options[opt['metadata']] = Option(opt)
    return options


def load_modes(options):
    ''' Loads all modes based on the given options '''
    modes = {}
    for option in options.values():
        for mode in option.modes:
            modes[mode] = modes.get(mode, []) + [option]
    return modes


OPTIONS = load_options(os.path.join(os.path.dirname(__file__), 'options.json'))
MODES = load_modes(OPTIONS)


class OptionsParser:
    '''
    This is the base object option parser. It can handles if required
    options are present, if there are bad mode options present and can
    insert default values.
    '''
    def __init__(self, mode, options):
        self.mode = mode
        self.options = MODES[self.mode]
        self.values = options

    def inject_default_values(self):
        for option in self.options:
            if option.metadata not in self.values:
                if option.default is not None:
                    self.values[option.metadata] = option.default

    def check_allowed_options(self):
        ''' Verifies if there are invalid options for the given mode '''
        for opt, value in self.values.items():
            option = OPTIONS[opt]
            option.validate_is_allowed(self.mode, value)

    def clean(self):
        self.inject_default_values()
        self.check_allowed_options()
        for option in self.options:
            self.values[option.metadata] = option.validate(
                self.mode, self.values.get(option.metadata))
        return self.values
