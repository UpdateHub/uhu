# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os


class Option:
    ''' A wrapper over each option within options.json '''

    def __init__(self, rules):
        self._rules = rules
        self.help = self._rules.get('help')
        self.default = self._rules.get('default')
        self.modes = tuple(self._rules.get('modes', []))
        self.metadata = self._rules.get('metadata')
        self.type = self._rules.get('type')
        self.cli = self._rules.get('cli')
        self.required_in = tuple(self._rules.get('required_in', []))
        self.requirements = self._rules.get('requirements')
        self.min = self._rules.get('min')
        self.max = self._rules.get('max')
        self.is_volatile = self._rules.get('is_volatile', False)
        self.verbose_name = self._rules.get('verbose-name')
        self.choices = self._rules.get('choices')


# Loads all options and modes from options.json
BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, 'options.json')) as fp:
    OPTIONS = {opt['metadata']: Option(opt) for opt in json.load(fp)}
MODES = sorted(set([mode for opt in OPTIONS.values() for mode in opt.modes]))


class OptionsParser:
    '''
    This is the base object option parser. It can handles if required
    options are present, if there are bad mode options present and can
    insert default values.
    '''

    def __init__(self, mode, options):
        self.mode = mode
        self.options = options

    def inject_default_values(self):
        for opt, conf in OPTIONS.items():
            if conf.default is None:
                continue
            if self.mode in conf.modes:
                if opt not in self.options:
                    self.options[opt] = conf.default

    def validate_extra_options(self):
        for option in self.options:
            opt = OPTIONS[option]
            if opt.is_volatile:
                continue
            if self.mode not in opt.modes:
                err = 'ERROR: {} is not valid in {} mode'
                raise ValueError(err.format(opt.metadata, self.mode))

    def validate_required_options(self):
        for opt in sorted(OPTIONS):
            conf = OPTIONS[opt]
            if self.mode not in conf.required_in:
                continue
            if opt not in self.options:
                err = 'ERROR: {} is required for {} mode'.format(
                    self.get_option_display(conf), self.mode)
                raise ValueError(err)

    def get_option_display(self, option):
        return option.metadata

    def clean(self):
        self.inject_default_values()
        self.validate_extra_options()
        self.validate_required_options()
        return self.options
