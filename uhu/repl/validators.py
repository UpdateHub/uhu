# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import re

from prompt_toolkit.validation import Validator

from .exceptions import ValidationError


# pylint: disable=too-few-public-methods
class ContainerValidator(Validator):

    def __init__(self, name, container, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.container = [str(elm) for elm in container]

    def validate(self, document):
        element = document.text.strip()
        if not element:
            message = '{} is required'.format(self.name)
            raise ValidationError(document, message)
        if element not in self.container:
            message = '"{}" is not a valid {}'.format(element, self.name)
            raise ValidationError(document, message)


# pylint: disable=too-few-public-methods
class ObjectUIDValidator(Validator):

    def validate(self, document):
        uid = document.text.split('#')[0].strip()
        if not uid:
            raise ValidationError(document, 'You must specify an object')
        if not uid.isdigit():
            message = '"{}" is not a valid object UID'.format(uid)
            raise ValidationError(document, message)


class ObjectOptionValueValidator(Validator):

    def __init__(self, option, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.option = option
        self.document = None
        self.value = None

    def validate(self, document):
        self.document = document
        # Normalize
        self.value = document.text.strip()

        # Checks if a blank value is valid
        if not self.value:
            if self.option.default is not None:
                return None
            if self.mode.is_required(self.option):
                raise ValidationError(document, 'You must provide a value')

        # Validates against metadata rules
        try:
            self.validate_value()
        except ValueError as err:
            raise ValidationError(document, str(err))

    def validate_value(self):
        if self.option.metadata == 'filename':
            self.validate_filename()
        elif self.option.metadata == 'target-type':
            self.validate_target_type()
        else:
            self.option.validate(self.value)

    def validate_filename(self):
        if not os.path.exists(self.value):
            message = '"{}" does not exist'.format(self.value)
            raise ValidationError(self.document, message)
        if os.path.isdir(self.value):
            raise ValidationError(self.document, 'Only files are allowed')

    def validate_target_type(self):
        if self.value not in self.mode.target_types:
            message = 'You must pass a valid target type (eg. {})'.format(
                ', '.join(self.mode.target_types))
            raise ValidationError(self.document, message)


class PackageUIDValidator(Validator):

    def validate(self, document):
        value = document.text.strip()
        if not value:
            message = 'You need to specify a package UID'
            raise ValidationError(document, message)
        if not re.match(r'[a-fA-F0-9]{64}', value):
            message = 'You need specify a valid package UID'
            raise ValidationError(document, message)
