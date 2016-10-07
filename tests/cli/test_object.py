# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

import click


from efu.core.options import Option
from efu.cli._object import ClickObjectOption, ClickOptionsParser


class ClickObjectTestCase(unittest.TestCase):

    def test_choice_type(self):
        option = Option({
            'metadata': 'name',
            'type': 'str',
            'choices': ['one', 'two', 'three'],
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertIsInstance(click_option.type, click.Choice)
        self.assertEqual(click_option.type.choices, ['one', 'two', 'three'])

    def test_int_type(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertEqual(click_option.type, click.INT)

    def test_str_type(self):
        option = Option({
            'metadata': 'name',
            'type': 'str',
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertEqual(click_option.type, click.STRING)

    def test_bool_type(self):
        option = Option({
            'metadata': 'name',
            'type': 'bool',
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertEqual(click_option.type, click.BOOL)

    def test_int_range_type(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'min': 10,
            'max': 20,
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertIsInstance(click_option.type, click.IntRange)
        self.assertEqual(click_option.type.min, 10)
        self.assertEqual(click_option.type.max, 20)

    def test_int_range_type_without_min(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'max': 20,
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertIsNone(click_option.type.min)
        self.assertEqual(click_option.type.max, 20)

    def test_int_range_type_without_max(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'min': 10,
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertEqual(click_option.type.min, 10)
        self.assertIsNone(click_option.type.max)

    def test_path_type(self):
        option = Option({
            'metadata': 'name',
            'type': 'path',
            'cli': ['--name']
        })
        click_option = ClickObjectOption(option)
        self.assertIsInstance(click_option.type, click.Path)
        self.assertFalse(click_option.type.readable)

    def test_default_value(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'cli': ['--name'],
            'default': 1234
        })
        click_option = ClickObjectOption(option)
        self.assertIsNone(click_option.default)
        self.assertEqual(click_option.default_lazy, 1234)

    def test_default_value_when_null_value(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'cli': ['--name'],
        })
        click_option = ClickObjectOption(option)
        self.assertIsNone(click_option.default)
        self.assertIsNone(click_option.default_lazy)

    def test_metadata_name(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'cli': ['--name'],
        })
        click_option = ClickObjectOption(option)
        self.assertEqual(click_option.metadata, 'name')

    def test_help_value(self):
        option = Option({
            'metadata': 'name',
            'type': 'int',
            'cli': ['--name'],
            'help': 'lorem ipsum'
        })
        click_option = ClickObjectOption(option)
        self.assertEqual(click_option.help, 'lorem ipsum')


class ClickOptionsParserTestCase(unittest.TestCase):

    def test_parser_options_has_no_None_values(self):
        options = {
            'target_device': '/dev/sda',
            'target_path': None,
            'filesystem': None,
            'seek': 10
        }
        parser = ClickOptionsParser('raw', options)
        self.assertEqual(len(parser.values), 2)
        self.assertNotIn('target_path', parser.values)
        self.assertNotIn('target-path', parser.values)
        self.assertNotIn('filesystem', parser.values)
        self.assertEqual(parser.values['target-device'], '/dev/sda')
        self.assertEqual(parser.values['seek'], 10)

    def test_parser_clean_returns_cleaned_object_options(self):
        options = {
            'target_device': '/dev/sda',
            'target_path': None,
            'filesystem': None,
            'seek': 10
        }
        parser = ClickOptionsParser('raw', options)
        cleaned = parser.clean()
        self.assertEqual(cleaned['target-device'], '/dev/sda')
        self.assertEqual(cleaned['seek'], 10)
        self.assertEqual(cleaned['chunk-size'], 131072)
        self.assertEqual(cleaned['count'], -1)
        self.assertEqual(cleaned['skip'], 0)
        self.assertFalse(cleaned['truncate'])

    def test_parser_raises_error_if_passed_extra_options(self):
        options = {
            'target_device': '/dev/sda',
            'target_path': 'extra',
        }
        parser = ClickOptionsParser('raw', options)
        with self.assertRaises(ValueError):
            parser.clean()

    def test_parser_raises_error_without_required_options(self):
        options = {'seek': 10}
        parser = ClickOptionsParser('raw', options)
        with self.assertRaises(ValueError):
            parser.clean()

    def test_parser_can_convert_options_to_metadata(self):
        options = {
            'target_path': '/home/music',
            'format': True,
        }
        parser = ClickOptionsParser('copy', options)
        self.assertEqual(parser.values['target-path'], '/home/music')
        self.assertTrue(parser.values['format?'])
