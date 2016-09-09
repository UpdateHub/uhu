# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu import utils

from ..base import delete_environment_variable, ObjectMockMixin, BaseTestCase


class UtilsTestCase(unittest.TestCase):

    def setUp(self):
        self.addCleanup(delete_environment_variable, 'EFU_CHUNK_SIZE')
        self.addCleanup(delete_environment_variable, 'EFU_SERVER_URL')
        self.addCleanup(delete_environment_variable, 'EFU_PACKAGE_FILE')

    def test_get_chunk_size_by_environment_variable(self):
        os.environ['EFU_CHUNK_SIZE'] = '1'
        observed = utils.get_chunk_size()
        self.assertEqual(observed, 1)

    def test_get_default_chunk_size(self):
        observed = utils.get_chunk_size()
        self.assertEqual(observed, utils._DEFAULT_CHUNK_SIZE)

    def test_get_server_url_by_environment_variable(self):
        os.environ['EFU_SERVER_URL'] = 'http://ossystems.com.br'
        observed = utils.get_server_url()
        self.assertEqual(observed, 'http://ossystems.com.br')

    def test_get_default_server_url(self):
        observed = utils.get_server_url()
        self.assertEqual(observed, utils._SERVER_URL)

    def test_can_get_url_with_path(self):
        os.environ['EFU_SERVER_URL'] = 'http://ossystems.com.br'
        observed = utils.get_server_url('/test')
        self.assertEqual(observed, 'http://ossystems.com.br/test')

    def test_can_get_package_file(self):
        observed = utils.get_package_file()
        self.assertEqual(observed, utils._PACKAGE_FILE)

    def test_can_get_package_file_by_environment_variable(self):
        os.environ['EFU_PACKAGE_FILE'] = '.test-efu'
        observed = utils.get_package_file()
        self.assertEqual(observed, '.test-efu')

    def test_yes_or_no_returns_yes_if_true(self):
        expected = 'yes'
        observed = utils.yes_or_no(True)
        self.assertEqual(expected, observed)

    def test_yes_or_no_returns_no_if_false(self):
        expected = 'no'
        observed = utils.yes_or_no(False)
        self.assertEqual(expected, observed)


class LocalConfigTestCase(ObjectMockMixin, BaseTestCase):

    def setUp(self):
        self.config_fn = '/tmp/.efu'
        os.environ[utils.LOCAL_CONFIG_VAR] = self.config_fn
        self.addCleanup(delete_environment_variable, utils.LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_file, self.config_fn)

    def test_can_get_local_config_file_by_environment_variable(self):
        observed = utils.get_local_config_file()
        self.assertEqual(observed, '/tmp/.efu')

    def test_can_get_default_local_config_file(self):
        del os.environ[utils.LOCAL_CONFIG_VAR]
        observed = utils.get_local_config_file()
        self.assertEqual(observed, utils.DEFAULT_LOCAL_CONFIG_FILE)

    def test_can_load_local_config(self):
        with open(self.config_fn, 'w') as fp:
            fp.write('{"test": 42}')
        config = utils.get_local_config()
        self.assertEqual(config['test'], 42)
