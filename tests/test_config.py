# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os

from uhu.config import Config, AUTH_SECTION
from uhu.utils import GLOBAL_CONFIG_VAR, PRIVATE_KEY_FN

from utils import UHUTestCase, EnvironmentFixtureMixin, FileFixtureMixin


class ConfigTestCase(FileFixtureMixin, EnvironmentFixtureMixin, UHUTestCase):

    def setUp(self):
        self.config_filename = self.create_file('')
        self.set_env_var(GLOBAL_CONFIG_VAR, self.config_filename)
        self.config = Config()

    def test_config_class_is_singleton(self):
        config1 = Config()
        config2 = Config()
        self.assertIs(config2, config1)
        self.assertEqual(config2, config1)

    def test_get_value_from_default_section(self):
        key = 'test_key'
        value = 'test_value'

        with open(self.config_filename, 'w') as fp:
            fp.write('[settings]\n')
            fp.write('{} = {}\n'.format(key, value))

        observed = self.config.get(key)
        self.assertEqual(observed, value)

    def test_get_value_from_different_section(self):
        section = 'auth'
        key = 'secret'
        value = 'super_secret'

        with open(self.config_filename, 'w') as fp:
            fp.write('[{}]\n'.format(section))
            fp.write('{} = {}\n'.format(key, value))

        observed = self.config.get(key, section=section)
        self.assertEqual(observed, value)

    def test_get_no_existent_key_returns_none(self):

        observed = self.config.get('invalid key')
        self.assertIsNone(observed)

        observed = self.config.get('invalid key', section='auth')
        self.assertIsNone(observed)

    def test_set_value(self):
        key = 'key'
        value = 'value'

        self.config.set(key, value)
        self.assertEqual(self.config.get(key), value)

    def test_set_value_in_a_different_section(self):
        section = 'auth'
        key = 'key'
        value = 'value'

        self.config.set(key, value, section=section)
        self.assertEqual(self.config.get(key, section=section), value)

    def test_can_set_and_get_crendetials(self):
        expected_access = 'id'
        expected_secret = 'secret'
        self.config.set_credentials(expected_access, expected_secret)
        access, secret = self.config.get_credentials()
        self.assertEqual(access, expected_access)
        self.assertEqual(secret, expected_secret)

    def test_can_set_and_get_private_key_path(self):
        self.config.set_private_key_path(__file__)
        path = self.config.get_private_key_path()
        self.assertEqual(path, __file__)

    def test_set_private_key_path_raises_error_if_invalid_path(self):
        # files = [not found file, directory]
        files = ['invalid', os.path.dirname(__file__)]
        for fn in files:
            with self.assertRaises(ValueError):
                self.config.set_private_key_path(fn)

    def test_can_get_private_key_path_from_environment(self):
        self.set_env_var(PRIVATE_KEY_FN, 'some-path')
        observed = self.config.get_private_key_path()
        self.assertEqual(observed, 'some-path')

    def test_set_command_does_not_override_previous_settings(self):
        self.config.set('foo', 'bar')
        self.config.set('bar', 'foo')

        self.assertEqual(self.config.get('foo'), 'bar')
        self.assertEqual(self.config.get('bar'), 'foo')

    def test_can_update_a_configuration(self):
        self.config.set('control', 'control')
        self.config.set('foo', 'bar')

        self.assertEqual(self.config.get('foo'), 'bar')
        self.assertEqual(self.config.get('control'), 'control')

        self.config.set('foo', 'foo bar')
        self.assertEqual(self.config.get('foo'), 'foo bar')
        self.assertEqual(self.config.get('control'), 'control')

    def test_get_credentials_raises_error_if_no_credentials_are_set(self):
        with self.assertRaises(ValueError):
            self.config.get_credentials()
