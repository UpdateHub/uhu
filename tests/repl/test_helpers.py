# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest
from unittest.mock import patch

from efu.core.object import Object
from efu.core.options import Option
from efu.core.package import Package
from efu.repl import helpers
from efu.repl.repl import EFURepl


class CheckerTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = EFURepl()

    def test_check_arg_returns_None_if_arg_is_passed(self):
        self.repl.arg = 'argument'
        self.assertIsNone(helpers.check_arg(self.repl, ''))

    def test_check_arg_raises_error_if_arg_is_not_passed(self):
        with self.assertRaises(ValueError):
            helpers.check_arg(self.repl, '')

    def test_check_version_returns_None_if_set(self):
        self.repl.package.version = '2.0'
        self.assertIsNone(helpers.check_version(self.repl))

    def test_check_version_raises_error_if_not_set(self):
        with self.assertRaises(ValueError):
            self.assertIsNone(helpers.check_version(self.repl))

    def test_check_product_returns_None_if_set(self):
        self.repl.package.product = 'product'
        self.assertIsNone(helpers.check_product(self.repl))

    def test_check_product_raises_error_if_not_set(self):
        with self.assertRaises(ValueError):
            self.assertIsNone(helpers.check_product(self.repl))


class PromptsTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = EFURepl()

    def test_set_product_prompt_returns_right_prompt(self):
        product = '123456789'
        expected = '[123456] efu> '
        observed = helpers.set_product_prompt(product)
        self.assertEqual(observed, expected)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_object_option(self, prompt):
        obj = Object(__file__, 'raw', {'target-device': '/'})
        prompt.return_value = 'target device'
        option = helpers.prompt_object_option(obj)
        self.assertEqual(option.metadata, 'target-device')

    @patch('efu.repl.helpers.prompt_object_option_value')
    def test_can_prompt_object_options(self, prompt):
        prompt.side_effect = ['always', '/dev/sda', 1000, 300, 100, 200, False]
        expected = {
            'target-device': '/dev/sda',
            'truncate': False,
            'seek': 100,
            'skip': 200,
            'count': 300,
            'chunk-size': 1000,
            'install-condition': 'always',
        }
        observed = helpers.prompt_object_options('raw')
        self.assertEqual(expected, observed)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_object_filename(self, prompt):
        prompt.return_value = '   filename.py  '
        expected = 'filename.py'
        observed = helpers.prompt_object_filename()
        self.assertEqual(expected, observed)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_object_mode(self, prompt):
        prompt.return_value = '   raw  '
        expected = 'raw'
        observed = helpers.prompt_object_mode()
        self.assertEqual(expected, observed)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_object_uid(self, prompt):
        prompt.return_value = '1# {}'.format(__file__)

        pkg = Package()
        pkg.objects.add_list()
        pkg.objects.add(__file__, 'raw', {'target-device': '/'})

        expected = 1
        observed = helpers.prompt_object_uid(pkg, 0)
        self.assertEqual(expected, observed)

    @patch('efu.repl.helpers.prompt_object_filename')
    def test_prompt_object_option_value_prompts_filename(self, prompt):
        prompt.return_value = __file__
        option = Option({'metadata': 'filename'})
        observed = helpers.prompt_object_option_value(option, 'raw')

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_package_uid(self, prompt):
        uid = '0' * 64
        prompt.return_value = uid
        observed = helpers.prompt_package_uid()
        self.assertEqual(observed, uid)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_pull(self, prompt):
        prompt.return_value = 'yes'
        observed = helpers.prompt_pull()
        self.assertEqual(observed, True)

    def test_can_parse_prompt_object_uid(self):
        uids = [0, 1, 2, 3]
        values = ['0# some name', '  1#  some-name  ', '2', '  3  ']
        for uid, value in zip(uids, values):
            observed = helpers.parse_prompt_object_uid(value)
            self.assertEqual(observed, uid)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_installation_set_returns_None_if_single(self, prompt):
        self.assertTrue(self.repl.package.objects.is_single())
        observed = helpers.prompt_installation_set(self.repl.package)
        self.assertIsNone(observed)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_installation_set_returns_int_if_not_single(self, prompt):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        self.assertFalse(self.repl.package.objects.is_single())
        helpers.prompt.return_value = '1'
        observed = helpers.prompt_installation_set(self.repl.package)
        self.assertEqual(observed, 1)

    def test_prompt_installation_returns_only_index_with_objects(self):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        self.repl.package.objects.add(
            __file__, 'raw', {'target-device': '/'}, index=1)
        observed = helpers.prompt_installation_set(
            self.repl.package, all_sets=False)
        self.assertEqual(observed, 1)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_package_mode(self, prompt):
        modes = ['single', 'active-inactive']
        values = ['single ', ' SinGle', 'active-inactive', ' ActivE-inactive ']
        for value in values:
            prompt.return_value = value
            observed = helpers.prompt_package_mode()
            self.assertIn(observed, modes)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_active_inactive_backend(self, prompt):
        prompt.return_value = 'u-boot'
        observed = helpers.prompt_active_inactive_backend()
        self.assertEqual(observed, 'u-boot')
