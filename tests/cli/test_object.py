# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

import click

from efu.core._options import (
    AbsolutePathOption, BooleanOption, IntegerOption, StringOption)
from efu.cli._object import ClickObjectOption


class ClickObjectTestCase(unittest.TestCase):

    def test_click_option_attributes(self):
        class Option(IntegerOption):
            metadata = 'name'
            cli = ['--name']
            default = 123
            help = 'lorem ipsum'
        click_option = ClickObjectOption(Option)
        self.assertIsNone(click_option.default)
        self.assertEqual(click_option.metadata, 'name')
        self.assertEqual(click_option.help, 'lorem ipsum')

    def test_bool_type(self):
        class Option(BooleanOption):
            metadata = 'name'
            cli = ['--name']

        click_option = ClickObjectOption(Option)
        self.assertEqual(click_option.type, click.BOOL)

    def test_int_type(self):
        class Option(IntegerOption):
            metadata = 'name'
            cli = ['--name']

        click_option = ClickObjectOption(Option)
        self.assertEqual(click_option.type, click.INT)

    def test_int_range_type(self):
        class Option(IntegerOption):
            metadata = 'name'
            min = 10
            max = 20
            cli = ['--name']
        click_option = ClickObjectOption(Option)
        self.assertIsInstance(click_option.type, click.IntRange)
        self.assertEqual(click_option.type.min, 10)
        self.assertEqual(click_option.type.max, 20)

    def test_int_range_type_without_min(self):
        class Option(IntegerOption):
            metadata = 'name'
            max = 20
            cli = ['--name']
        click_option = ClickObjectOption(Option)
        self.assertIsNone(click_option.type.min)
        self.assertEqual(click_option.type.max, 20)

    def test_int_range_type_without_max(self):
        class Option(IntegerOption):
            metadata = 'name'
            min = 10
            cli = ['--name']
        click_option = ClickObjectOption(Option)
        self.assertEqual(click_option.type.min, 10)
        self.assertIsNone(click_option.type.max)

    def test_path_type(self):
        class Option(AbsolutePathOption):
            metadata = 'name'
            cli = ['--name']
        click_option = ClickObjectOption(Option)
        self.assertIsInstance(click_option.type, click.Path)
        self.assertFalse(click_option.type.readable)

    def test_str_type(self):
        class Option(StringOption):
            metadata = 'name'
            cli = ['--name']

        click_option = ClickObjectOption(Option)
        self.assertEqual(click_option.type, click.STRING)

    def test_string_with_choices_type(self):
        class Option(StringOption):
            metadata = 'name'
            choices = ['one', 'two', 'three']
            cli = ['--name']

        click_option = ClickObjectOption(Option)
        self.assertIsInstance(click_option.type, click.Choice)
        self.assertEqual(click_option.type.choices, ['one', 'two', 'three'])
