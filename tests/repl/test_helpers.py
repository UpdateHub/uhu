# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest
from unittest.mock import patch

from efu.core.object import Object
from efu.repl import helpers
from efu.repl.repl import EFURepl


class PromptsTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = EFURepl()

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_object_option(self, prompt):
        obj = Object(__file__, 'raw', {'target-device': '/'})
        prompt.return_value = 'target device'
        option = helpers.prompt_object_option(obj)
        self.assertEqual(option.metadata, 'target-device')

    @patch('efu.repl.helpers.prompt')
    def test_prompt_object_option_raises_error_if_invalid_option(self, prompt):
        obj = Object(__file__, 'raw', {'target-device': '/'})
        prompt.return_value = 'invalid-option'
        with self.assertRaises(ValueError):
            helpers.prompt_object_option(obj)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_package_uid(self, prompt):
        uid = '0' * 64
        prompt.return_value = uid
        observed = helpers.prompt_package_uid()
        self.assertEqual(observed, uid)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_package_uid_raises_error_with_empty_value(self, prompt):
        prompt.return_value = ''
        with self.assertRaises(ValueError):
            helpers.prompt_package_uid()

    def test_can_parse_prompt_object_uid(self):
        uids = [0, 1, 2, 3]
        values = ['0# some name', '  1#  some-name  ', '2', '  3  ']
        for uid, value in zip(uids, values):
            observed = helpers.parse_prompt_object_uid(value)
            self.assertEqual(observed, uid)

    def test_parse_prompt_object_uid_raises_error_if_invalid_uid(self):
        with self.assertRaises(ValueError):
            helpers.parse_prompt_object_uid('invalid-value')

    @patch('efu.repl.helpers.prompt')
    def test_prompt_installation_set_returns_None_if_single(self, prompt):
        self.assertTrue(self.repl.package.objects.is_single())
        observed = helpers.prompt_installation_set(self.repl)
        self.assertIsNone(observed)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_installation_set_returns_int_if_multiple(self, prompt):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        self.assertFalse(self.repl.package.objects.is_single())
        helpers.prompt.return_value = '1'
        observed = helpers.prompt_installation_set(self.repl)
        self.assertEqual(observed, 1)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_installation_raises_error_if_invalid_index(self, prompt):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        helpers.prompt.return_value = 'invalid'
        with self.assertRaises(ValueError):
            helpers.prompt_installation_set(self.repl)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_installation_raises_error_with_invalid_index(self, prompt):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        helpers.prompt.return_value = '11234123'
        with self.assertRaises(ValueError):
            helpers.prompt_installation_set(self.repl)

    def test_prompt_installation_returns_only_index_with_objects(self):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        self.repl.package.objects.add(
            __file__, 'raw', {'target-device': '/'}, index=1)
        observed = helpers.prompt_installation_set(self.repl, empty=False)
        self.assertEqual(observed, 1)

    def test_prompt_installation_raises_error_when_objects_is_empty(self):
        self.repl.package.objects.add_list()
        self.repl.package.objects.add_list()
        with self.assertRaises(ValueError):
            helpers.prompt_installation_set(self.repl, empty=False)

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_package_mode(self, prompt):
        modes = ['single', 'active-backup']
        values = ['  single ', '  SinGle', 'active-backup', '  ActivE-baCKup ']
        for value in values:
            prompt.return_value = value
            observed = helpers.prompt_package_mode()
            self.assertIn(observed, modes)

    @patch('efu.repl.helpers.prompt')
    def test_prompt_package_mode_raises_error_if_invalid_mode(self, prompt):
        prompt.return_value = 'invalid-mode'
        with self.assertRaises(ValueError):
            helpers.prompt_package_mode()

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_active_backup_backend(self, prompt):
        prompt.return_value = 'grub2'
        observed = helpers.prompt_active_backup_backend()
        self.assertEqual(observed, 'grub2')

    @patch('efu.repl.helpers.prompt')
    def test_prompt_active_backup_backend_raises_if_invalid(self, prompt):
        prompt.return_value = 'invalid-backend'
        with self.assertRaises(ValueError):
            helpers.prompt_active_backup_backend()
