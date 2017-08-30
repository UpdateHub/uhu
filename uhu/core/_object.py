# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import math
import os

from ..utils import call, get_chunk_size

from ._options import Options
from .compression import compression_to_metadata
from .install_condition import InstallCondition
from .validators import validate_options


class Modes:
    registry = {}

    @classmethod
    def get(cls, name):
        obj_class = cls.registry.get(name)
        if obj_class is None:
            raise ValueError('There is no {} object class.'.format(name))
        return obj_class

    @classmethod
    def names(cls):
        return sorted([mode for mode in cls.registry])


class ObjectType(type):

    def __init__(cls, classname, bases, methods):
        super().__init__(classname, bases, methods)
        # register class into modes registry
        if getattr(cls, 'mode', None) is not None:
            Modes.registry[cls.mode] = cls

        if cls.allow_compression:
            cls.options.append('compressed')
            cls.options.append('required-uncompressed-size')
        if cls.allow_install_condition:
            cls.options.append('install-condition')
            cls.options.append('install-condition-version')
            cls.options.append('install-condition-pattern-type')
            cls.options.append('install-condition-pattern')
            cls.options.append('install-condition-seek')
            cls.options.append('install-condition-buffer-size')
            cls.string_template.insert(0, ('install-condition', ()))
            cls.string_template.insert(
                1, ('install-condition-pattern-type', ()))
            cls.string_template.insert(2, (
                'install-condition-pattern',
                ('install-condition-seek', 'install-condition-buffer-size')))

        # converts strings to Option classes
        cls.options = [Options.get(opt) for opt in cls.options]
        cls.required_options = [
            Options.get(opt) for opt in cls.required_options]
        cls.string_template = [
            (Options.get(opt), [Options.get(child) for child in children])
            for opt, children in cls.string_template]


class BaseObject(metaclass=ObjectType):
    mode = None
    allow_compression = False
    allow_install_condition = False
    options = []
    required_options = []
    string_template = tuple()
    target_types = None

    @classmethod
    def is_required(cls, option):
        return option in cls.required_options

    def __init__(self, values):
        self._values = validate_options(self, values)
        self.chunk_size = get_chunk_size()
        self.md5 = None

    def to_template(self):
        template = {opt.metadata: value
                    for opt, value in self._values.items()
                    if not opt.volatile}
        template['mode'] = self.mode
        return template

    def to_metadata(self, callback=None):
        self.load(callback)
        metadata = {opt.metadata: value for opt, value in self._values.items()}
        metadata['mode'] = self.mode
        metadata.update(self._metadata_install_condition(metadata))
        metadata.update(self._metadata_compression())
        return metadata

    def _metadata_install_condition(self, metadata):
        if not self.allow_install_condition:
            return {}
        return InstallCondition(metadata).to_metadata()

    def _metadata_compression(self):
        if not self.allow_compression:
            return {}
        return compression_to_metadata(self.filename)

    def to_upload(self):
        return {
            'filename': self['filename'],
            'size': self['size'],
            'sha256sum': self['sha256sum'],
            'md5': self.md5,
            'chunks': len(self)
        }

    @property
    def filename(self):
        """Shortcut to returns object filename option."""
        return self['filename']

    @property
    def size(self):
        """Returns the size of object file."""
        return os.path.getsize(self.filename)

    @property
    def exists(self):
        """Checks if file exsits."""
        return os.path.exists(self.filename)

    def update(self, option, value):
        """Updates a given option value."""
        self[option] = value

    def load(self, callback=None):
        """Reads object to set its size, sha256sum and MD5."""
        sha256sum = hashlib.sha256()
        md5 = hashlib.md5()
        for chunk in self:
            sha256sum.update(chunk)
            md5.update(chunk)
            call(callback, 'object_read')
        self['sha256sum'] = sha256sum.hexdigest()
        self['size'] = self.size
        self.md5 = md5.hexdigest()

    def __setitem__(self, key, value):
        try:
            option = Options.get(key)
        except ValueError:
            raise TypeError('You must provide a registered option')
        try:
            self._values[option] = option.validate(value)
        except ValueError:
            raise TypeError('You must provide a valid value.')
        values = {option.metadata: value
                  for option, value in self._values.items()}
        values[key] = value
        self._values = validate_options(self, values)

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise TypeError('You must provide a option metadata name')
        try:
            option = Options.get(key)
        except ValueError:
            raise TypeError('You must provide a registered option')
        if option not in self.options:
            raise ValueError(
                '{} does not support {}'.format(self.mode, option))
        return self._values.get(option)

    def __len__(self):
        """The size of a object is the number of chunks it has."""
        return math.ceil(self.size/self.chunk_size)

    def __iter__(self):
        """Yields every single chunk."""
        with open(self.filename, 'br') as fp:
            for chunk in iter(lambda: fp.read(self.chunk_size), b''):
                yield chunk

    def __str__(self):
        lines = ['{} [mode: {}]\n'.format(self.filename, self.mode)]
        for option, suboptions in self.string_template:
            value = self[option.metadata]
            if value is None:
                continue
            name = '{}:'.format(option.verbose_name)
            suboptions_value = ''
            if suboptions:
                suboptions_line = []
                for suboption in suboptions:
                    suboption_value = self[suboption.metadata]
                    if suboption_value is None:
                        continue
                    suboptions_line.append('{}: {}'.format(
                        suboption.verbose_name,
                        suboption.humanize(suboption_value)))
                if suboptions_line:
                    suboptions_value = ' [{}]'.format(
                        ', '.join(suboptions_line))
            lines.append('    {:<25}{}{}'.format(
                name, option.humanize(value), suboptions_value))
        return '\n'.join(lines)
