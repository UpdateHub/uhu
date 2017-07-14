# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import re

from prompt_toolkit.validation import Validator

from .exceptions import ValidationError


def validate_filename(filename):
    if not os.path.exists(filename):
        raise ValidationError(
            message='"{}" does not exist'.format(filename))
    if os.path.isdir(filename):
        raise ValidationError(message='Only files are allowed')


# pylint: disable=too-few-public-methods
class ContainerValidator(Validator):

    def __init__(self, name, container, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.container = [str(elm) for elm in container]

    def validate(self, document):
        element = document.text.strip()
        if not element:
            raise ValidationError(message='{} is required'.format(self.name))
        if element not in self.container:
            raise ValidationError(
                message='"{}" is not a valid {}'.format(element, self.name))


# pylint: disable=too-few-public-methods
class ObjectUIDValidator(Validator):

    def validate(self, document):
        uid = document.text.split('#')[0].strip()
        if not uid:
            raise ValidationError(message='You must specify an object')
        if not uid.isdigit():
            raise ValidationError(
                message='"{}" is not a valid object UID'.format(uid))


class ObjectOptionValueValidator(Validator):

    def __init__(self, option, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.option = option

    def validate(self, document):
        value = document.text.strip()
        if not value:
            if self.option.default is not None:
                return None
            if self.mode.is_required(self.option):
                raise ValidationError(message='You must provide a value')
        try:
            if self.option.metadata == 'filename':
                validate_filename(value)
            else:
                self.option.validate(value, self.mode)
        except ValueError as err:
            raise ValidationError(message=str(err))


class PackageUIDValidator(Validator):

    def validate(self, document):
        uid = document.text.strip()

        if not uid:
            raise ValidationError(message='You need to specify a package UID')
        if not re.match(r'[a-fA-F0-9]{64}', uid):
            raise ValidationError(
                message='You need specify a valid package UID')
