# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import os
import unittest
from unittest.mock import Mock

from prompt_toolkit.validation import ValidationError

from uhu.core._options import Options
from uhu.core.object import Modes
from uhu.repl import validators


def document(text):
    """Creates a prompt_toolkit Document mock."""
    doc = Mock()
    doc.text = text
    return doc


class ContainerValidatorTestCase(unittest.TestCase):

    def test_valid_option_returns_None(self):
        validator = validators.ContainerValidator('x', [1, 2, 3])
        self.assertIsNone(validator.validate(document('1')))

    def test_empty_value_raises_error(self):
        validator = validators.ContainerValidator('x', [1, 2, 3])
        with self.assertRaises(ValidationError):
            validator.validate(document(''))

    def test_non_existent_options_raises_error(self):
        validator = validators.ContainerValidator('x', [1, 2, 3])
        with self.assertRaises(ValidationError):
            validator.validate(document('non-existent'))


class ObjectUIDValidatorTestCase(unittest.TestCase):

    validator = validators.ObjectUIDValidator()

    def test_valid_object_uid_returns_None(self):
        text = '1# filename.py'
        self.assertIsNone(self.validator.validate(document(text)))

    def test_empty_value_raises_error(self):
        with self.assertRaises(ValidationError):
            self.validator.validate(document(''))

    def test_invalid_object_uid_raises_error(self):
        with self.assertRaises(ValidationError):
            self.validator.validate(document('invalid_object_uid'))


class ObjectOptionValueValidator(unittest.TestCase):

    def test_valid_value_returns_None(self):
        option = Options.get('format?')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        for value in ['y', 'yes', 'n', 'no']:
            self.assertIsNone(validator.validate(document(value)))

    def test_empty_value_returns_None_if_option_has_default(self):
        option = Options.get('format?')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        self.assertIsNone(validator.validate(document('')))

    def test_empty_value_raises_error_if_required_and_has_no_default(self):
        option = Options.get('target')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        with self.assertRaises(ValidationError):
            validator.validate(document(''))

    def test_invalid_value_raises_error(self):
        option = Options.get('truncate')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        with self.assertRaises(ValidationError):
            validator.validate(document('not-an-absolut-path'))

    def test_filename_option_requires_a_valid_filename(self):
        option = Options.get('filename')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        dirname = os.path.dirname(__file__)
        with self.assertRaises(ValidationError):
            validator.validate(document('invalid-file'))
        with self.assertRaises(ValidationError):
            validator.validate(document(dirname))

    def test_raises_when_invalid_choice(self):
        option = Options.get('filesystem')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        with self.assertRaises(ValidationError):
            validator.validate(document('invalid-filesystem'))

    def test_raises_when_invalid_target_type(self):
        option = Options.get('target-type')
        validator = validators.ObjectOptionValueValidator(
            option, Modes.get('copy'))
        with self.assertRaises(ValidationError):
            validator.validate(document('invalid-target-type'))


class PackageUIDValidatorTestCase(unittest.TestCase):

    validator = validators.PackageUIDValidator()

    def test_valid_value_returns_None(self):
        text = hashlib.sha256(b'').hexdigest()
        self.assertIsNone(self.validator.validate(document(text)))

    def test_empty_value_raises_error(self):
        with self.assertRaises(ValidationError):
            self.validator.validate(document(''))

    def test_invalid_value_raises_error(self):
        with self.assertRaises(ValidationError):
            self.validator.validate(document('invalid-package-uid'))
