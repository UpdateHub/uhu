# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest
from configparser import ConfigParser

from click.testing import CliRunner

from efu.config import Config, Sections
from efu.utils import LOCAL_CONFIG_VAR
from efu.cli.config import (
    cleanup_command, get_command, set_command, init_command)
from efu.utils import GLOBAL_CONFIG_VAR

from utils import FileFixtureMixin, EnvironmentFixtureMixin, EFUTestCase


class ConfigCommandTestCase(
        FileFixtureMixin, EnvironmentFixtureMixin, EFUTestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_filename = self.create_file('')
        self.set_env_var(GLOBAL_CONFIG_VAR, self.config_filename)
        self.config = Config()

    def test_can_set_a_configuration(self):
        self.runner.invoke(set_command, args=['foo', 'bar'])
        config = ConfigParser()
        config.read(self.config_filename)
        self.assertEqual(config['settings']['foo'], 'bar')

    def test_can_set_configuration_in_another_section(self):
        section = 'upload'
        self.runner.invoke(
            set_command, args=['foo', 'bar', '--section', section])
        config = ConfigParser()
        config.read(self.config_filename)
        self.assertEqual(config.get(section, 'foo'), 'bar')

    def test_can_get_a_configuration(self):
        with open(self.config_filename, 'w') as fp:
            fp.write('[settings]\n')
            fp.write('foo = bar\n\n')
        result = self.runner.invoke(get_command, args=['foo'])
        self.assertEqual(result.output.strip(), 'bar')

    def test_can_get_configuration_from_another_section(self):
        with open(self.config_filename, 'w') as fp:
            fp.write('[auth]\n')
            fp.write('foo = bar\n\n')
        result = self.runner.invoke(
            get_command, args=['foo', '--section', 'auth'])
        self.assertEqual(result.output.strip(), 'bar')

    def test_can_set_many_values_and_retrieve_them_later(self):
        self.runner.invoke(set_command, args=['foo', 'bar'])
        self.runner.invoke(set_command, args=['bar', 'foo'])
        config = ConfigParser()
        config.read(self.config_filename)
        self.assertEqual(config.get('settings', 'foo'), 'bar')
        self.assertEqual(config.get('settings', 'bar'), 'foo')

    def test_return_none_when_getting_inexistent_configuration(self):
        result = self.runner.invoke(get_command, args=['no-existent'])
        self.assertEqual(result.output, '')

    def test_can_set_init_commandial_configuration(self):
        self.runner.invoke(init_command, input='1234\nasdf')
        config = ConfigParser()
        config.read(self.config_filename)
        id_ = config.get(Sections.AUTH, 'access_id')
        secret = config.get(Sections.AUTH, 'access_secret')
        self.assertEqual(id_, '1234')
        self.assertEqual(secret, 'asdf')


class CleanupCommandTestCase(unittest.TestCase):

    def setUp(self):
        os.environ[LOCAL_CONFIG_VAR] = '.efu-test'
        self.runner = CliRunner()
        self.addCleanup(os.environ.pop, LOCAL_CONFIG_VAR)

    def test_can_cleanup_efu_files(self):
        open('.efu-test', 'w').close()
        self.assertTrue(os.path.exists('.efu-test'))
        self.runner.invoke(cleanup_command)
        self.assertFalse(os.path.exists('.efu-test'))

    def test_cleanup_command_returns_0_if_successful(self):
        open('.efu-test', 'w').close()
        result = self.runner.invoke(cleanup_command)
        self.assertEqual(result.exit_code, 0)

    def test_cleanup_command_returns_1_if_package_is_already_deleted(self):
        result = self.runner.invoke(cleanup_command)
        self.assertEqual(result.exit_code, 1)
