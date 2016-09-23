# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import unittest

from efu.core.options import OPTIONS, Option, OptionsParser


class OptionTestCase(unittest.TestCase):

    def test_can_create_new_option(self):
        conf = json.loads('''{
            "modes": ["tarball", "copy"],
            "required_in": ["copy"],
            "metadata": "format?",
            "type": "bool",
            "default": false,
            "help": "Spam with eggs"
        }''')
        opt = Option(conf)
        self.assertEqual(opt.metadata, 'format?')
        self.assertEqual(opt.default, False)
        self.assertEqual(opt.help, conf['help'])
        self.assertEqual(opt.modes, ('tarball', 'copy'))
        self.assertEqual(opt.required_in, ('copy',))


class OptionsParserTestCase(unittest.TestCase):

    def test_can_inject_default_values(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertEqual(len(parser.options), 1)
        parser.inject_default_values()
        self.assertEqual(len(parser.options), 7)
        self.assertIsNotNone(parser.options.get('compressed'))
        self.assertIsNotNone(parser.options.get('seek'))
        self.assertIsNotNone(parser.options.get('skip'))
        self.assertIsNotNone(parser.options.get('truncate'))
        self.assertIsNotNone(parser.options.get('chunk-size'))
        self.assertIsNotNone(parser.options.get('seek'))
        self.assertIsNotNone(parser.options.get('count'))

    def test_inject_default_values_do_not_overwrite_passed_values(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'truncate': True,
        })
        parser.inject_default_values()
        self.assertTrue(parser.options['truncate'])

    def test_validate_extra_options_returns_None_if_valid(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertIsNone(parser.validate_extra_options())

    def test_validate_extra_options_raises_error_if_invalid(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'target-path': '/dev/sdb'  # not valid in raw mode
        })
        with self.assertRaises(ValueError):
            parser.validate_extra_options()

    def test_validate_required_options_returns_None_if_valid(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertIsNone(parser.validate_required_options())

    def test_validate_required_options_raises_error_if_invalid(self):
        parser = OptionsParser('raw', {})  # missing target-device
        with self.assertRaises(ValueError):
            parser.validate_required_options()

    def test_get_option_display_returns_option_metadata_name(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        observed = parser.get_option_display(OPTIONS['target-device'])
        self.assertEqual(observed, 'target-device')

    def test_clean_returns_options_with_default_values(self):
        parser = OptionsParser('raw', {'target-device': '/dev/sda'})
        self.assertEqual(len(parser.options), 1)
        options = parser.clean()
        self.assertEqual(len(options), 7)

    def test_clean_raises_error_if_passed_extra_options(self):
        parser = OptionsParser('raw', {
            'target-device': '/dev/sda',
            'target-path': '/dev/sdb'  # not valid in raw mode
        })
        with self.assertRaises(ValueError):
            parser.clean()

    def test_clean_raises_error_if_missing_required_options(self):
        parser = OptionsParser('raw', {})  # missing target-device
        with self.assertRaises(ValueError):
            parser.clean()
