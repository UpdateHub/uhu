# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu import utils

from ..base import delete_environment_variable


class UtilsTestCase(unittest.TestCase):

    def setUp(self):
        self.addCleanup(delete_environment_variable, 'EFU_CHUNK_SIZE')
        self.addCleanup(delete_environment_variable, 'EFU_SERVER_URL')
        self.addCleanup(delete_environment_variable, 'EFU_PACKAGE_FILE')
        self.addCleanup(delete_environment_variable, utils.LOCAL_CONFIG_VAR)

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

    def test_can_get_local_config_file_by_environment_variable(self):
        os.environ[utils.LOCAL_CONFIG_VAR] = '/tmp/.efu'
        observed = utils.get_local_config_file()
        self.assertEqual(observed, '/tmp/.efu')

    def test_can_get_default_local_config_file(self):
        observed = utils.get_local_config_file()
        self.assertEqual(observed, utils.DEFAULT_LOCAL_CONFIG_FILE)

    def test_can_load_local_config(self):
        config_fn = '/tmp/.efu'
        os.environ[utils.LOCAL_CONFIG_VAR] = config_fn
        self.addCleanup(os.remove, config_fn)
        with open(config_fn, 'w') as fp:
            fp.write('{"test": 42}')
        config = utils.get_local_config()
        self.assertEqual(config['test'], 42)
