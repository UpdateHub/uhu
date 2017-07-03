# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from uhu.config import Config, AUTH_SECTION
from uhu.utils import GLOBAL_CONFIG_VAR

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

    def test_set_initial_configuration(self):
        expected_id = 'id'
        expected_secret = 'secret'

        self.config.set_initial(expected_id, expected_secret)

        observed_id = self.config.get('access_id', section=AUTH_SECTION)
        observed_secret = self.config.get('access_secret', AUTH_SECTION)

        self.assertEqual(observed_id, expected_id)
        self.assertEqual(observed_secret, expected_secret)

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
