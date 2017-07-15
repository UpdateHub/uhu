# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import unittest
from unittest.mock import patch

from uhu import utils

from utils import UHUTestCase, FileFixtureMixin, EnvironmentFixtureMixin


class UtilsTestCase(EnvironmentFixtureMixin, UHUTestCase):

    def setUp(self):
        self.addCleanup(self.remove_env_var, utils.CHUNK_SIZE_VAR)
        self.addCleanup(self.remove_env_var, utils.GLOBAL_CONFIG_VAR)
        self.addCleanup(self.remove_env_var, utils.LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_env_var, utils.SERVER_URL_VAR)

    def test_get_chunk_size_by_environment_variable(self):
        os.environ[utils.CHUNK_SIZE_VAR] = '1'
        observed = utils.get_chunk_size()
        self.assertEqual(observed, 1)

    def test_get_default_chunk_size(self):
        observed = utils.get_chunk_size()
        self.assertEqual(observed, utils.DEFAULT_CHUNK_SIZE)

    def test_get_server_url_by_environment_variable(self):
        os.environ[utils.SERVER_URL_VAR] = 'http://ossystems.com.br'
        observed = utils.get_server_url()
        self.assertEqual(observed, 'http://ossystems.com.br')

    def test_get_default_server_url(self):
        observed = utils.get_server_url()
        self.assertEqual(observed, utils.DEFAULT_SERVER_URL)

    def test_can_get_url_with_path(self):
        os.environ[utils.SERVER_URL_VAR] = 'http://ossystems.com.br'
        observed = utils.get_server_url('/test')
        self.assertEqual(observed, 'http://ossystems.com.br/test')

    def test_get_server_url_strips_slashes(self):
        os.environ[utils.SERVER_URL_VAR] = 'http://ossystems.com.br/'
        observed = utils.get_server_url()
        self.assertEqual(observed, 'http://ossystems.com.br')

    def test_can_get_default_global_config_file(self):
        observed = utils.get_global_config_file()
        self.assertEqual(observed, utils.DEFAULT_GLOBAL_CONFIG_FILE)

    def test_can_get_config_file_by_environment_variable(self):
        os.environ[utils.GLOBAL_CONFIG_VAR] = '/tmp/super_file'
        observed = utils.get_global_config_file()
        self.assertEqual(observed, '/tmp/super_file')


class StringUtilsTestCase(unittest.TestCase):

    def test_yes_or_no_returns_yes_if_true(self):
        expected = 'yes'
        observed = utils.yes_or_no(True)
        self.assertEqual(expected, observed)

    def test_yes_or_no_returns_no_if_false(self):
        expected = 'no'
        observed = utils.yes_or_no(False)
        self.assertEqual(expected, observed)

    def test_can_indent_text(self):
        expected = '1\n  2\n  3'
        observed = utils.indent('1\n2\n3\n', 2)
        self.assertEqual(expected, observed)

    def test_can_indent_all_lines(self):
        expected = '  1\n  2\n  3\n'
        observed = utils.indent('1\n2\n3\n', 2, all_lines=True)
        self.assertEqual(expected, observed)


class LocalConfigTestCase(
        EnvironmentFixtureMixin, FileFixtureMixin, UHUTestCase):

    def setUp(self):
        self.config_fn = '/tmp/.uhu'
        os.environ[utils.LOCAL_CONFIG_VAR] = self.config_fn
        self.addCleanup(self.remove_env_var, utils.LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_file, self.config_fn)

    def test_can_get_local_config_file_by_environment_variable(self):
        observed = utils.get_local_config_file()
        self.assertEqual(observed, '/tmp/.uhu')

    def test_can_get_default_local_config_file(self):
        del os.environ[utils.LOCAL_CONFIG_VAR]
        observed = utils.get_local_config_file()
        self.assertEqual(observed, utils.DEFAULT_LOCAL_CONFIG_FILE)

    def test_can_load_local_config(self):
        with open(self.config_fn, 'w') as fp:
            fp.write('{"test": 42}')
        config = utils.get_local_config()
        self.assertEqual(config['test'], 42)

    def test_can_remove_package_file(self):
        open(self.config_fn, 'w').close()
        self.assertTrue(os.path.exists(self.config_fn))
        utils.remove_local_config()
        self.assertFalse(os.path.exists(self.config_fn))

    def test_remove_package_file_raises_error_when_file_already_deleted(self):
        self.assertFalse(os.path.exists(self.config_fn))
        with self.assertRaises(FileNotFoundError):
            utils.remove_local_config()
