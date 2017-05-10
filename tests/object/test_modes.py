# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import unittest

from uhu.core._base import BaseObject
from uhu.core._options import BooleanOption
from uhu.core.modes import CopyObject


# Nested options

class GrandParent(BooleanOption):
    metadata = 'grandparent'


class Parent(BooleanOption):
    metadata = 'parent'
    requirements = {GrandParent: True}


class Child(BooleanOption):
    metadata = 'child'
    requirements = {Parent: True}


class VolatileOption(BooleanOption):
    metadata = 'volatile'
    volatile = True


# Nested options with default values

class ParentWithDefault(BooleanOption):
    metadata = 'parent-default'
    requirements = {GrandParent: False}
    default = False


class ChildWithDefault(BooleanOption):
    metadata = 'child-default'
    requirements = {ParentWithDefault: False}
    default = False


class ObjectFixture(BaseObject):
    mode = 'object-mode'
    options = ['grandparent', 'parent', 'child', 'volatile']


class ObjectFixtureWithDefault(BaseObject):
    options = ['grandparent', 'parent-default', 'child-default']


class ObjectsTestCase(unittest.TestCase):

    def test_invalid_options_raises_error(self):
        with self.assertRaises(ValueError):
            CopyObject({
                'filename': __file__,
                'target': 'device',
                'target': '/',
                'target-path': '/yey',
                'filesystem': 'ext4',
                'truncate': True,
            })

    def test_missing_option_validation(self):
        with self.assertRaises(ValueError):
            CopyObject({
                'filename': __file__,
                'target-type': 'device',
                'target': '/',
                'target-path': '/yey',
            })

    def test_can_inject_default_values(self):
        obj = CopyObject({
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
        })
        self.assertEqual(obj['format?'], False)
        self.assertIsNone(obj['format-options'])

    def test_with_format_True_and_without_format_options_is_valid(self):
        obj = CopyObject({
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
            'format?': True
        })
        self.assertEqual(obj['format?'], True)
        self.assertIsNone(obj['format-options'])

    def test_with_format_True_and_format_options_is_valid(self):
        obj = CopyObject({
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
            'format?': True,
            'format-options': 'all',
        })
        self.assertEqual(obj['format?'], True)
        self.assertEqual(obj['format-options'], 'all')

    def test_format_options_raises_error_if_format_is_None(self):
        with self.assertRaises(ValueError):
            CopyObject({
                'filename': __file__,
                'target-type': 'device',
                'target': '/',
                'target-path': '/yey',
                'filesystem': 'ext4',
                'format-options': 'all'
            })

    def test_format_options_raisees_error_if_format_is_False(self):
        with self.assertRaises(ValueError):
            CopyObject({
                'filename': __file__,
                'target-type': 'device',
                'target': '/',
                'target-path': '/yey',
                'filesystem': 'ext4',
                'format?': False,
                'format-options': 'all',
            })

    def test_can_get_option_by_object_subscription(self):
        obj = CopyObject({
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
            'format?': True,
        })
        self.assertEqual(obj['format?'], True)
        self.assertIsNone(obj['format-options'])
        with self.assertRaises(TypeError):
            obj[1]
        with self.assertRaises(TypeError):
            obj['unregistered_option']
        with self.assertRaises(ValueError):
            obj['count']

    def test_can_set_option_by_object_subscription(self):
        obj = CopyObject({
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
        })
        self.assertEqual(obj['format?'], False)
        obj['format?'] = True
        self.assertEqual(obj['format?'], True)
        with self.assertRaises(TypeError):
            obj['invalid_option'] = 'invalid'
        with self.assertRaises(TypeError):
            obj['format?'] = 'invalid value'
        self.assertEqual(obj['format?'], True)

        # obj validation
        obj['format?'] = False
        with self.assertRaises(ValueError):
            obj['format-options'] = 'all'

    def test_metadata_representation(self):
        with open(__file__, 'br') as fp:
            sha256sum = hashlib.sha256(fp.read()).hexdigest()

        expected = {
            'mode': 'copy',
            'filename': __file__,
            'size': os.path.getsize(__file__),
            'sha256sum': sha256sum,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
            'format?': False,
        }
        obj = CopyObject({
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
        })
        metadata = obj.metadata()
        self.assertEqual(metadata, expected)

    def test_metadata_representation_with_compression(self):
        base_dir = os.path.join(
            os.path.dirname(__file__), '../fixtures/compressed/')
        uncompressed_fn = os.path.join(base_dir, 'base.txt')
        compressed_fn = os.path.join(base_dir, 'base.txt.gz')
        with open(compressed_fn, 'br') as fp:
            sha256sum = hashlib.sha256(fp.read()).hexdigest()
        obj = CopyObject({
            'filename': compressed_fn,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
        })
        expected = {
            'mode': 'copy',
            'filename': compressed_fn,
            'size': os.path.getsize(compressed_fn),
            'sha256sum': sha256sum,
            'target-type': 'device',
            'target': '/',
            'target-path': '/yey',
            'filesystem': 'ext4',
            'format?': False,
            'compressed': True,
            'required-uncompressed-size': os.path.getsize(uncompressed_fn),
        }
        self.assertEqual(obj.metadata(), expected)

    def test_nested_option_validation_for_valid_options(self):
        valid_options = [
            {
                'grandparent': True,
                'parent': None,
                'child': None,
            },
            {
                'grandparent': False,
                'parent': None,
                'child': None,
            },
            {
                'grandparent': True,
                'parent': False,
                'child': None,
            },
            {
                'grandparent': True,
                'parent': True,
                'child': None,
            },
            {
                'grandparent': True,
                'parent': True,
                'child': True
            },
            {
                'grandparent': True,
                'parent': True,
                'child': False
            },
        ]
        for options in valid_options:
            obj = ObjectFixture(options)
            self.assertEqual(obj['grandparent'], options['grandparent'])
            self.assertEqual(obj['parent'], options['parent'])
            self.assertEqual(obj['child'], options['child'])

    def test_nested_option_validation_for_invalid_options(self):
        invalid_options = [
            {
                'grandparent': None,
                'parent': False,
                'child': None,
            },
            {
                'grandparent': False,
                'parent': False,
                'child': None,
            },
            {
                'grandparent': False,
                'parent': True,
                'child': None,
            },
            {
                'grandparent': None,
                'parent': None,
                'child': False,
            },
            {
                'grandparent': None,
                'parent': False,
                'child': False,
            },
            {
                'grandparent': None,
                'parent': True,
                'child': False,
            },
            {
                'grandparent': False,
                'parent': True,
                'child': False,
            },
            {
                'grandparent': True,
                'parent': False,
                'child': True
            },
        ]
        for options in invalid_options:
            with self.assertRaises(ValueError):
                ObjectFixture(options)

    def test_can_insert_nested_default_values(self):
        options = {
            'grandparent': False,
            'parent-default': None,  # should be injected
            'child-default': None,  # should be injected
        }
        obj = ObjectFixtureWithDefault(options)
        self.assertEqual(obj['grandparent'], False)
        self.assertEqual(obj['parent-default'], False)
        self.assertEqual(obj['child-default'], False)

    def test_valid_nested_options_with_default_injection_validation(self):
        valid_options = [
            {
                'grandparent': True,
                'parent-default': None,  # should not be injected
                'child-default': None,  # should not be injected
            },
            {
                'grandparent': None,  # should not be injected
                'parent-default': None,  # should not be injected
                'child-default': None,  # should not be injected
            },
            {
                'grandparent': False,
                'parent-default': True,
                'child-default': None,  # should not be injected
            }
        ]
        for options in valid_options:
            obj = ObjectFixtureWithDefault(options)
            self.assertEqual(obj['grandparent'], options['grandparent'])
            self.assertEqual(obj['parent-default'], options['parent-default'])
            self.assertEqual(obj['child-default'], options['child-default'])

    def test_invalid_nested_options_with_default_injection_validation(self):
        invalid_options = [
            {
                'grandparent': None,
                'parent-default': None,  # grandparent is missing, can't inject
                'child-default': False,  # requires parent False
            },
            {
                'grandparent': None,
                'parent-default': True,  # grandparent requirement is missing
                'child-default': None,
            },
            {
                'grandparent': True,
                'parent-default': None,  # grandparent is True, can't inject
                'child-default': False,  # requires parent False
            },
            {
                'grandparent': True,
                'parent-default': False,  # requires grandparent False
                'child-default': None,
            },
        ]
        for options in invalid_options:
            with self.assertRaises(ValueError):
                ObjectFixtureWithDefault(options)

    def test_can_serialize_as_template(self):
        obj = ObjectFixture({
            'grandparent': True,
            'parent': True,
            'child': True,
            'volatile': True,
        })
        expected = {
            'mode': 'object-mode',
            'grandparent': True,
            'parent': True,
            'child': True,
        }
        observed = obj.template()
        self.assertEqual(observed, expected)
