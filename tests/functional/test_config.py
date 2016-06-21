# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import configparser
import os
import subprocess
import unittest


class ConfigCommandTestCase(unittest.TestCase):

    def setUp(self):
        self.filename = os.path.expanduser('~/.efu')
        self._backup = None

        if os.path.exists(self.filename):
            self._backup = open(self.filename).read()

        self.config = configparser.ConfigParser()

    def tearDown(self):
        os.remove(self.filename)
        if self._backup:
            with open(self.filename, 'w') as fp:
                fp.write(self._backup)

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
        self.config.read(self.filename)
        self.assertEqual(self.config['settings']['foo'], 'bar')

    def test_can_set_configuration_in_another_section(self):
        command = ['efu', 'config', 'set', 'foo', 'bar', '--section', 'auth']
        subprocess.call(command)
        self.config.read(self.filename)
        self.assertEqual(self.config['auth']['foo'], 'bar')

    def test_can_get_a_configuration(self):
        with open(self.filename, 'w') as fp:
            fp.write('[settings]\n')
            fp.write('foo = bar\n\n')

        command = ['efu', 'config', 'get', 'foo']
        response = subprocess.check_output(command)
        value = response.decode().strip()
        self.assertEqual(value, 'bar')

    def test_can_get_configuration_from_another_section(self):
        with open(self.filename, 'w') as fp:
            fp.write('[auth]\n')
            fp.write('foo = bar\n\n')

        command = ['efu', 'config', 'get', 'foo', '--section', 'auth']
        response = subprocess.check_output(command)
        value = response.decode().strip()
        self.assertEqual(value, 'bar')

    def test_configuration_file_persists(self):
        subprocess.call(['efu', 'config', 'set', 'foo', 'bar'])
        subprocess.call(['efu', 'config', 'set', 'bar', 'foo'])
        with open(self.filename) as fp:
            print(fp.read())

        config = configparser.ConfigParser()
        config.read(self.filename)
        self.assertEqual(config['settings']['foo'], 'bar')
        self.assertEqual(config['settings']['bar'], 'foo')

    def test_return_none_when_getting_inexistent_configuration(self):
        command = ['efu', 'config', 'get', 'no-existent']
        response = subprocess.check_output(command)
        self.assertEqual(response.decode(), '')

    def test_can_set_initial_configuration(self):
        subprocess.check_output(['efu', 'config', 'init'], input=b'1234\nasdf')

        self.config.read(self.filename)
        id = self.config['auth']['access_id']
        secret = self.config['auth']['access_secret']

        self.assertEqual(id, '1234')
        self.assertEqual(secret, 'asdf')
