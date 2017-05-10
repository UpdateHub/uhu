# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

from uhu.core._options import (
    Options, BaseOption, IntegerOption, AbsolutePathOption, BooleanOption,
    StringOption)
from uhu.core.options import FormatOptionsOption


class OptionsTestCase(unittest.TestCase):

    def test_can_get_option(self):
        observed = Options.get('format-options')
        self.assertEqual(observed, FormatOptionsOption)

    def test_get_option_raises_error_if_unknown_option(self):
        with self.assertRaises(ValueError):
            Options.get('unknown')

    def test_options_must_implement_validate_method(self):
        class Option(BaseOption):
            pass
        option = Option()
        with self.assertRaises(NotImplementedError):
            option.validate(None)


class AbsolutePathOptionTestCase(unittest.TestCase):

    def test_can_validate(self):
        for value in ['/', '/dev/sda/', '/dev/sda', '/ asdf.12 3?!.asdf.']:
            self.assertEqual(AbsolutePathOption.validate(value), value)

    def test_validate_raises_error_if_invalid(self):
        for value in [1, True, 'not-a-path']:
            with self.assertRaises(ValueError):
                AbsolutePathOption.validate(value)

    def test_relative_path_is_invalid(self):
        for value in ['dev/sda', '../dev/sda', './dev/sda']:
            with self.assertRaises(ValueError):
                AbsolutePathOption.validate(value)


class BooleanOptionTestCase(unittest.TestCase):

    def test_can_validate_true_values(self):
        for value in [True, 'y', 'yes']:
            self.assertEqual(BooleanOption.validate(value), True)

    def test_can_validate_false_values(self):
        for value in [False, 'n', 'no']:
            self.assertEqual(BooleanOption.validate(value), False)

    def test_validate_raises_error_if_invalid(self):
        for value in [1, 0, 'bad', ['1']]:
            with self.assertRaises(ValueError):
                BooleanOption.validate(value)


class IntegerOptionTestCase(unittest.TestCase):

    def setUp(self):
        default_min = IntegerOption.min
        default_max = IntegerOption.max
        self.addCleanup(setattr, IntegerOption, 'min', default_min)
        self.addCleanup(setattr, IntegerOption, 'max', default_max)

    def test_can_validate(self):
        for value in [1, -1, '1', '-1']:
            self.assertEqual(IntegerOption.validate(value), int(value))

    def test_validate_raises_error_if_invalid(self):
        for value in [3.14, '3.14', 'asdf', True, 'a']:
            with self.assertRaises(ValueError):
                IntegerOption.validate(value)

    def test_can_validate_with_range(self):
        IntegerOption.min = 0
        IntegerOption.max = 10
        # valid values
        for value in [0, 5, 10]:
            self.assertEqual(IntegerOption.validate(value), value)
        # invalid values
        for value in [-1, 11]:
            with self.assertRaises(ValueError):
                IntegerOption.validate(value)

    def test_can_validate_with_only_min_range(self):
        IntegerOption.min = 0
        for value in [0, 5, 10]:
            self.assertEqual(IntegerOption.validate(value), value)
        with self.assertRaises(ValueError):
            IntegerOption.validate(-1)

    def test_can_validate_with_only_max_range(self):
        IntegerOption.max = 10
        for value in [0, 5, 10]:
            self.assertEqual(IntegerOption.validate(value), value)
        with self.assertRaises(ValueError):
            IntegerOption.validate(11)


class StringOptionTestCase(unittest.TestCase):

    def setUp(self):
        default_choices = StringOption.choices
        self.addCleanup(setattr, StringOption, 'choices', default_choices)

        default_min = StringOption.min
        self.addCleanup(setattr, StringOption, 'min', default_min)

        default_max = StringOption.max
        self.addCleanup(setattr, StringOption, 'max', default_max)

    def test_can_validate(self):
        for value in [1, 'spam', 'eggs']:
            self.assertEqual(StringOption.validate(value), str(value))

    def test_can_validate_with_choices(self):
        StringOption.choices = ['spam', 'eggs', 'ham']
        for value in ['spam', 'eggs', 'ham']:
            self.assertEqual(StringOption.validate(value), value)
        values = ['pizza', 'ice-cream', 'chocolate']
        for value in values:
            with self.assertRaises(ValueError):
                StringOption.validate(value)

    def test_can_validate_with_length(self):
        StringOption.min = 3
        StringOption.max = 5
        # valid values
        for value in ['123', '1234', '12345']:
            self.assertEqual(StringOption.validate(value), value)
        # invalid values
        for value in ['', '12', '123456']:
            with self.assertRaises(ValueError):
                StringOption.validate(value)

    def test_can_validate_with_min_length_only(self):
        StringOption.min = 3
        for value in ['123', '1234', '12345']:
            self.assertEqual(StringOption.validate(value), value)
        with self.assertRaises(ValueError):
            for value in ['', '1', '12']:
                StringOption.validate(value)

    def test_can_validate_with_max_length_only(self):
        StringOption.max = 5
        for value in ['123', '1234', '12345']:
            self.assertEqual(StringOption.validate(value), value)
        with self.assertRaises(ValueError):
            StringOption.validate('123456')
