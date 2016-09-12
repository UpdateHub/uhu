# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import unittest

from jsonschema.exceptions import ValidationError

from efu.metadata.metadata import ObjectMetadata, validate

from ..base import ObjectMockMixin, BaseTestCase


class MetadataValidatorTestCase(ObjectMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.schema = self.create_file(json.dumps({
            'type': 'object',
            'properties': {
                'test': {
                    'type': 'string',
                }
            },
            'additionalProperties': False,
            'required': ['test']
        }).encode())

    def test_validate_returns_None_when_valid(self):
        obj = {'test': 'ok'}
        self.assertIsNone(validate(self.schema, obj))

    def test_validate_returns_False_when_invalid(self):
        with self.assertRaises(ValidationError):
            self.assertFalse(validate(self.schema, {}))
        with self.assertRaises(ValidationError):
            self.assertFalse(validate(self.schema, {'test': 1}))
        with self.assertRaises(ValidationError):
            self.assertFalse(validate(self.schema, {'test': 'ok', 'extra': 2}))


class ObjectMetadataTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.filename = 'spam.py'
        self.sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        self.size = 4

    def test_can_get_metadata_option_by_attr(self):
        options = {
            'install-mode': 'raw',
            'seek': 0,
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertEqual(metadata.install_mode, 'raw')
        self.assertEqual(metadata.seek, 0)

    def test_getattr_raises_error_if_no_option_is_found(self):
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, None)
        with self.assertRaises(AttributeError):
            metadata.install_mode

    def test_object_metadata_serialized(self):
        options = {
            'install-mode': 'raw',
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        expected = {
            'filename': self.filename,
            'sha256sum': self.sha256sum,
            'size': 4,
            'install-mode': 'raw',
            'target-device': 'device',
        }
        observed = metadata.serialize()
        self.assertEqual(observed, expected)

    def test_object_metadata_is_valid_returns_True_when_valid(self):
        options = {
            'install-mode': 'raw',
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertTrue(metadata.is_valid())

    def test_object_metadata_is_invalid_with_invalid_metadata(self):
        options = {
            'install-mode': 'raw',
            'seek': 'base-value (should be a number)',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertFalse(metadata.is_valid())

    def test_object_metadata_is_invalid_when_install_mode_is_missing(self):
        options = {
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertFalse(metadata.is_valid())

    def test_object_metadata_is_invalid_with_invalid_install_mode(self):
        options = {
            'install-mode': 'bad-raw',
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertFalse(metadata.is_valid())
