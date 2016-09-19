# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import unittest

from jsonschema.exceptions import ValidationError

from efu.core import Object
from efu.metadata.metadata import ObjectMetadata, PackageMetadata, validate

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
            'mode': 'raw',
            'seek': 0,
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertEqual(metadata.mode, 'raw')
        self.assertEqual(metadata.seek, 0)

    def test_getattr_raises_error_if_no_option_is_found(self):
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, None)
        with self.assertRaises(AttributeError):
            metadata.mode

    def test_object_metadata_serialized(self):
        options = {
            'mode': 'raw',
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        expected = {
            'filename': self.filename,
            'sha256sum': self.sha256sum,
            'size': 4,
            'mode': 'raw',
            'target-device': 'device',
        }
        observed = metadata.serialize()
        self.assertEqual(observed, expected)

    def test_object_metadata_is_valid_returns_True_when_valid(self):
        options = {
            'mode': 'raw',
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertTrue(metadata.is_valid())

    def test_object_metadata_is_invalid_with_invalid_metadata(self):
        options = {
            'mode': 'raw',
            'seek': 'base-value (should be a number)',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertFalse(metadata.is_valid())

    def test_object_metadata_is_invalid_when_mode_is_missing(self):
        options = {
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertFalse(metadata.is_valid())

    def test_object_metadata_is_invalid_with_invalid_mode(self):
        options = {
            'mode': 'bad-raw',
            'target-device': 'device',
        }
        metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, options)
        self.assertFalse(metadata.is_valid())


class PackageMetadataTestCase(ObjectMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.fn = self.create_file(b'spam')
        self.sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        self.version = '2.0'
        self.options = {
            'mode': 'raw',
            'filename': self.fn,
            'target-device': '/dev/sda1',
            'truncate': False,
            'count': 1024,
            'seek': 512,
            'skip': 256,
            'chunk-size': 128
        }
        self.objects = [Object(self.fn, self.options)]
        self.product = 'cfe2be1c64b0387500853de0f48303e3de7b1c6f1508dc719eeafa0d41c36722'  # nopep8

    def test_metadata_serialized(self):
        expected = {
            'product': self.product,
            'version': self.version,
            'objects': [
                {
                    'mode': 'raw',
                    'filename': self.fn,
                    'size': 4,
                    'sha256sum': self.sha256sum,
                    'target-device': '/dev/sda1',
                    'truncate': False,
                    'count': 1024,
                    'seek': 512,
                    'skip': 256,
                    'chunk-size': 128
                }
            ]
        }
        metadata = PackageMetadata(self.product, self.version, self.objects)
        observed = metadata.serialize()
        self.assertEqual(observed, expected)

    def test_metadata_is_valid_returns_True_when_valid(self):
        metadata = PackageMetadata(self.product, self.version, self.objects)
        self.assertTrue(metadata.is_valid())

    def test_metadata_is_valid_returns_False_when_invalid(self):
        self.product = 1
        self.version = None
        metadata = PackageMetadata(self.product, self.version, self.objects)
        self.assertFalse(metadata.is_valid())

    def test_metadata_is_valid_returns_False_object_is_invalid(self):
        self.options = {
            'mode': 'bad-option',
            'filename': self.fn,
        }
        self.objects = [Object(self.fn, self.options)]
        metadata = PackageMetadata(self.product, self.version, self.objects)
        self.assertFalse(metadata.is_valid())
