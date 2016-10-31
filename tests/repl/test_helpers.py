# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest
from unittest.mock import patch

from efu.core.object import Object
from efu.repl import helpers


class PromptsTestCase(unittest.TestCase):

    @patch('efu.repl.helpers.prompt')
    def test_can_prompt_object_option(self, prompt):
        obj = Object(__file__, 'raw', {'target-device': '/'})
        prompt.return_value = 'target-device'
        observed = helpers.prompt_object_option(obj)
        self.assertEqual(observed, 'target-device')

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
