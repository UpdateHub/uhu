# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest
from efu.core.options import OptionsParser


class OptionsParserTestCase(unittest.TestCase):

    def test_can_remove_null_values(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'mount-options': None
        })
        self.assertEqual(len(parser.values), 2)
        self.assertIn('mount-options', parser.values)
        parser.remove_null_values()
        self.assertEqual(len(parser.values), 1)
        self.assertNotIn('mount-options', parser.values)

    def test_can_inject_default_values(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertEqual(len(parser.values), 1)
        parser.inject_default_values()
        self.assertEqual(len(parser.values), 7)
        self.assertIsNotNone(parser.values.get('seek'))
        self.assertIsNotNone(parser.values.get('skip'))
        self.assertIsNotNone(parser.values.get('truncate'))
        self.assertIsNotNone(parser.values.get('chunk-size'))
        self.assertIsNotNone(parser.values.get('seek'))
        self.assertIsNotNone(parser.values.get('count'))
        self.assertIsNotNone(parser.values.get('install-condition'))

    def test_inject_default_values_do_not_overwrite_passed_values(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'truncate': True,
        })
        parser.inject_default_values()
        self.assertTrue(parser.values['truncate'])

    def test_check_allowed_options_returns_None_if_valid(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertIsNone(parser.check_allowed_options())

    def test_check_allowed_options_raises_error_if_invalid(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'target-path': '/dev/sdb'  # not valid in raw mode
        })
        with self.assertRaises(ValueError):
            parser.check_allowed_options()

    def test_check_options_requirements_returns_None_if_valid(self):
        parser = OptionsParser('copy', {
            'format?': True,
            'format-options': '--all'  # requires format? True
        })
        self.assertIsNone(parser.check_options_requirements())

    def test_check_options_requirements_raises_error_if_invalid(self):
        parser = OptionsParser('copy', {
            'format?': False,
            'format-options': '--all'  # requires format? True
        })
        with self.assertRaises(ValueError):
            parser.check_options_requirements()

    def test_check_options_requirements_returns_None_if_not_required(self):
        options = {
            'target-device': '/dev/sda',
            'target-path': '/boot',
            'filesystem': 'ext4'
        }  # no format? passed
        parser = OptionsParser('copy', options)
        self.assertIsNone(parser.check_options_requirements())

    def test_clean_returns_options_with_default_values(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertEqual(len(parser.values), 1)
        options = parser.clean()
        self.assertEqual(len(options), 7)

    def test_clean_returns_options_without_null_values(self):
        parser = OptionsParser('copy', {
            'target-device': '/dev/sda',
            'target-path': '/',
            'filesystem': 'ext4',
            'mount-options': None
        })
        self.assertIn('mount-options', parser.values)
        options = parser.clean()
        self.assertNotIn('mount-options', options)

    def test_clean_raises_error_if_passed_not_allowed_options(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'target-path': '/dev/sdb'  # not allowed in raw mode
        })
        with self.assertRaises(ValueError):
            parser.clean()

    def test_clean_raises_error_if_missing_required_options(self):
        parser = OptionsParser('raw', {})  # missing target-device
        with self.assertRaises(ValueError):
            parser.clean()
