# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest
from unittest.mock import partial, patch

from efu.config.config import Config


class ConfigTestCase(unittest.TestCase):

    def setUp(self):
        self.config_filename = '/tmp/efu_dot_file'
        Config.CONFIG_FILENAME = self.config_filename

    def tearDown(self):
        os.remove(self.config_filename)

    def test_get_value_from_default_section(self):
        key = 'test_key'
        value = 'test_value'

        with open(self.config_filename, 'w') as fp:
            fp.write('[settings]\n')
            fp.write('{} = {}\n'.format(key, value))

        config = Config()
        observed = config.get(key)
        self.assertEqual(observed, value)

    def test_get_value_from_different_section(self):
        section = 'auth'
        key = 'secret'
        value = 'super_secret'

        with open(self.config_filename, 'w') as fp:
            fp.write('[{}]\n'.format(section))
            fp.write('{} = {}\n'.format(key, value))

        config = Config()
        observed = config.get(key, section=section)
        self.assertEqual(observed, value)

    def test_get_no_existent_key_returns_none(self):
        config = Config()
        observed = config.get('invalid key')
        self.assertIsNone(observed)

        observed = config.get('invalid key', section='auth')
        self.assertIsNone(observed)

    def test_set_value(self):
        key = 'key'
        value = 'value'
        config = Config()
        config.set(key, value)
        self.assertEqual(config.get(key), value)

    def test_set_value_in_a_different_section(self):
        section = 'auth'
        key = 'key'
        value = 'value'
        config = Config()
        config.set(key, value, section=section)
        self.assertEqual(config.get(key, section=section), value)
