# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import unittest

from efu.core.options import Option


class OptionTestCase(unittest.TestCase):

    def test_can_create_new_option(self):
        conf = json.loads('''{
            "modes": ["tarball", "copy"],
            "required_in": ["copy"],
            "metadata": "format?",
            "type": "bool",
            "default": false,
            "help": "Spam with eggs",
            "verbose-name": "format device"
        }''')
        opt = Option(conf)
        self.assertEqual(opt.metadata, 'format?')
        self.assertEqual(opt.default, False)
        self.assertEqual(opt.help, conf['help'])
        self.assertEqual(opt.modes, ('tarball', 'copy'))
        self.assertEqual(opt.required_in, ('copy',))
        self.assertEqual(opt.verbose_name, 'format device')

    def test_can_validate_true_bool_values(self):
        option = Option({
            'type': 'bool',
        })
        values = [True, 'y', 'yes']
        for value in values:
            self.assertEqual(option.validate_bool(value), True)

    def test_can_validate_false_bool_values(self):
        option = Option({
            'type': 'bool',
        })
        values = [False, 'n', 'no']
        for value in values:
            self.assertEqual(option.validate_bool(value), False)

    def test_validate_bool_raises_error_if_invalid(self):
        option = Option({
            'type': 'bool',
        })
        values = [1, 0, 'bad', ['1']]
        for value in values:
            with self.assertRaises(ValueError):
                option.validate_bool(value)

    def test_can_validate_int_values(self):
        option = Option({
            'type': 'int'
        })
        values = [1, -1, '1', '-1']
        for value in values:
            self.assertEqual(option.validate_int(value), int(value))

    def test_can_validate_int_value_with_range(self):
        option = Option({
            'type': 'int',
            'min': 0,
            'max': 10
        })
        values = [0, 5, 10]
        for value in values:
            self.assertEqual(option.validate_int(value), value)
        values = [-1, 11]
        for value in values:
            with self.assertRaises(ValueError):
                option.validate_int(value)

    def test_can_validate_int_value_with_only_min(self):
        option = Option({
            'type': 'int',
            'min': 0,
        })
        values = [0, 5, 10]
        for value in values:
            self.assertEqual(option.validate_int(value), value)
        with self.assertRaises(ValueError):
            option.validate_int(-1)

    def test_can_validate_int_value_with_only_max(self):
        option = Option({
            'type': 'int',
            'max': 10,
        })
        values = [0, 5, 10]
        for value in values:
            self.assertEqual(option.validate_int(value), value)
        with self.assertRaises(ValueError):
            option.validate_int(11)

    def test_validate_int_raises_error_if_invalid(self):
        option = Option({
            'type': 'int',
        })
        values = [3.14, '3.14', 'asdf', True, 'a']
        for value in values:
            with self.assertRaises(ValueError):
                option.validate_int(value)

    def test_can_validate_path(self):
        option = Option({
            'type': 'path'
        })
        values = ['/', '/dev/sda/', '/dev/sda', '/ asdf.12 3?!.asdf.']
        for value in values:
            self.assertEqual(option.validate_path(value), value)

    def test_validate_path_raises_error_if_invalid(self):
        option = Option({
            'type': 'path'
        })
        values = [1, True, 'dev/sda']
        for value in values:
            with self.assertRaises(ValueError):
                option.validate_path(value)

    def test_can_validate_str(self):
        option = Option({
            'type': 'str'
        })
        values = [1, 'spam', 'eggs']
        for value in values:
            self.assertEqual(option.validate_str(value), str(value))

    def test_can_validate_str_with_choices(self):
        option = Option({
            'type': 'str',
            'choices': ['spam', 'eggs', 'ham']
        })
        values = ['spam', 'eggs', 'ham']
        for value in values:
            self.assertEqual(option.validate_str(value), value)
        values = ['pizza', 'ice-cream', 'chocolate']
        for value in values:
            with self.assertRaises(ValueError):
                option.validate_str(value)

    def test_can_validate_if_option_is_allowed(self):
        option = Option({
            'type': 'str',
            'choices': ['spam', 'eggs', 'ham'],
            'modes': ['copy'],
            'is_volatile': False
        })
        self.assertIsNone(option.validate_is_allowed('copy', 'spam'))
        with self.assertRaises(ValueError):
            option.validate_is_allowed('raw', 'spam')

    def test_can_validate_if_option_is_required(self):
        option = Option({
            'type': 'str',
            'choices': ['spam', 'eggs', 'ham'],
            'required_in': ['copy'],
        })
        self.assertIsNone(option.validate_is_required('copy', 'spam'))
        with self.assertRaises(ValueError):
            option.validate_is_required('copy', None)
