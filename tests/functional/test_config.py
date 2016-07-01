# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import subprocess
import unittest
from configparser import ConfigParser

from efu.config.config import Sections

from ..base import ConfigTestCaseMixin


class ConfigCommandTestCase(ConfigTestCaseMixin, unittest.TestCase):

    def test_config_command_exists(self):
        response = subprocess.check_output(['efu', 'config', '--help'])
        self.assertIn('config', response.decode())

    def test_config_set_command_exists(self):
        response = subprocess.check_output(['efu', 'config', 'set', '--help'])
        self.assertIn('config', response.decode())

    def test_config_get_command_exists(self):
        response = subprocess.check_output(['efu', 'config', 'get', '--help'])
        self.assertIn('config', response.decode())

    def test_can_set_a_configuration(self):
        command = ['efu', 'config', 'set', 'foo', 'bar']
        subprocess.call(command)

        config = ConfigParser()
        config.read(self.config_filename)
        self.assertEqual(config['settings']['foo'], 'bar')

    def test_can_set_configuration_in_another_section(self):
        section = 'upload'
        command = ['efu', 'config', 'set', 'foo', 'bar', '--section', section]
        subprocess.call(command)

        config = ConfigParser()
        config.read(self.config_filename)

        self.assertEqual(config.get(section, 'foo'), 'bar')

    def test_can_get_a_configuration(self):
        with open(self.config_filename, 'w') as fp:
            fp.write('[settings]\n')
            fp.write('foo = bar\n\n')

        command = ['efu', 'config', 'get', 'foo']
        response = subprocess.check_output(command)
        value = response.decode().strip()
        self.assertEqual(value, 'bar')

    def test_can_get_configuration_from_another_section(self):
        with open(self.config_filename, 'w') as fp:
            fp.write('[auth]\n')
            fp.write('foo = bar\n\n')

        command = ['efu', 'config', 'get', 'foo', '--section', 'auth']
        response = subprocess.check_output(command)
        value = response.decode().strip()
        self.assertEqual(value, 'bar')

    def test_can_set_many_values_and_retrieve_them_later(self):
        subprocess.call(['efu', 'config', 'set', 'foo', 'bar'])
        subprocess.call(['efu', 'config', 'set', 'bar', 'foo'])

        with open(self.config_filename) as fp:
            print(fp.read())

        config = ConfigParser()
        config.read(self.config_filename)

        self.assertEqual(config.get('settings', 'foo'), 'bar')
        self.assertEqual(config.get('settings', 'bar'), 'foo')

    def test_return_none_when_getting_inexistent_configuration(self):
        command = ['efu', 'config', 'get', 'no-existent']
        response = subprocess.check_output(command)
        self.assertEqual(response.decode(), '')

    def test_can_set_initial_configuration(self):
        subprocess.check_output(['efu', 'config', 'init'], input=b'1234\nasdf')

        config = ConfigParser()
        config.read(self.config_filename)

        id_ = config.get(Sections.AUTH, 'access_id')
        secret = config.get(Sections.AUTH, 'access_secret')

        self.assertEqual(id_, '1234')
        self.assertEqual(secret, 'asdf')
