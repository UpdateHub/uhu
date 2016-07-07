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
