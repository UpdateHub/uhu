# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import re


class Options:
    registry = {}

    @classmethod
    def get(cls, name):
        option = cls.registry.get(name)
        if option is None:
            raise ValueError('There is no {} option.'.format(name))
        return option

    @classmethod
    def all(cls):
        return [option for option in cls.registry.values()]


class OptionType(type):

    def __init__(cls, classname, bases, methods):
        super().__init__(classname, bases, methods)
        if getattr(cls, 'metadata', None) is not None:
            Options.registry[cls.metadata] = cls


class BaseOption(metaclass=OptionType):
    metadata = None
    help = None
    default = None
    verbose_name = None
    cli = None
    # volatile determines if a option must be not exported or
    # considered when loading an object.
    volatile = False
    # For now, requirements only supports "by value" requirement type
    # and it is implemented with a dict, where the key is the option
    # to check value, and the value is what will be checked against
    # option value.
    requirements = {}
    # symmetric determines if this option can have more than on value,
    # one for each installation set.
    symmetric = True

    choices = None
    min = None
    max = None

    type_name = None

    @classmethod
    def validate(cls, value):
        """Must convert, validate and return a value."""
        raise NotImplementedError

    @classmethod
    def humanize(cls, value):
        return value


class AbsolutePathOption(BaseOption):
    type_name = 'absolute_path'

    @classmethod
    def validate(cls, value):
        """Validates if value is an absolute path."""
        value = str(value)
        result = re.match(r'^/[^\0]*', value)
        if result is None:
            err = '"{}" is not a valid absolut path'
            raise ValueError(err.format(value))
        return value


class BooleanOption(BaseOption):
    type_name = 'boolean'

    @classmethod
    def validate(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ['yes', 'y']:
                return True
            if value in ['no', 'n']:
                return False
        raise ValueError('Only y, yes, n and no values are allowed')

    @classmethod
    def humanize(cls, value):
        return 'yes' if value else 'no'


class IntegerOption(BaseOption):
    type_name = 'integer'

    min = None
    max = None

    @classmethod
    def validate(cls, value):
        # This must be checked this way since isintance(True, int) is
        # True in Python.
        # pylint: disable=unidiomatic-typecheck
        if type(value) not in (int, str):
            raise ValueError('Only integers are allowed')
        try:
            value = int(value)
        except ValueError:
            raise ValueError('Only integers are allowed')
        if cls.min is not None and value < cls.min:
            err = '{} is lesser than {}'
            raise ValueError(err.format(value, cls.min))
        if cls.max is not None and value > cls.max:
            err = '{} is greater than {}'
            raise ValueError(err.format(value, cls.max))
        return value


class StringOption(BaseOption):
    type_name = 'string'

    min = None
    max = None
    choices = []

    @classmethod
    def validate(cls, value):
        value = str(value)
        if cls.choices and value not in cls.choices:
            err = '"{}" is not in {}'
            raise ValueError(err.format(value, cls.choices))
        if cls.min is not None and len(value) < cls.min:
            err = '{} length is lesser than {}'
            raise ValueError(err.format(value, cls.min))
        if cls.max is not None and len(value) > cls.max:
            err = '{} length is greater than {}'
            raise ValueError(err.format(value, cls.max))
        return value

    @classmethod
    def humanize(cls, value):
        return '"{}"'.format(value)
