# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import base64
import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from uhu import utils

from utils import UHUTestCase, FileFixtureMixin, EnvironmentFixtureMixin


class UtilsTestCase(EnvironmentFixtureMixin, UHUTestCase):

    def setUp(self):
        self.addCleanup(self.remove_env_var, utils.CHUNK_SIZE_VAR)
        self.addCleanup(self.remove_env_var, utils.GLOBAL_CONFIG_VAR)
        self.addCleanup(self.remove_env_var, utils.LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_env_var, utils.SERVER_URL_VAR)
        self.addCleanup(self.remove_env_var, utils.CUSTOM_CA_CERTS_VAR)

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

    def test_can_get_custom_ca_certificates_variable(self):
        os.environ[utils.CUSTOM_CA_CERTS_VAR] = '/tmp/ca-certificates.crt'
        observed = utils.get_custom_ca_certs_file()
        self.assertEqual(observed, '/tmp/ca-certificates.crt')

    def test_get_default_custom_ca_certificates_variable(self):
        observed = utils.get_custom_ca_certs_file()
        self.assertEqual(observed, None)


class StringUtilsTestCase(unittest.TestCase):

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

    def test_can_remove_package_file(self):
        open(self.config_fn, 'w').close()
        self.assertTrue(os.path.exists(self.config_fn))
        utils.remove_local_config()
        self.assertFalse(os.path.exists(self.config_fn))

    def test_remove_package_file_raises_error_when_file_already_deleted(self):
        self.assertFalse(os.path.exists(self.config_fn))
        with self.assertRaises(FileNotFoundError):
            utils.remove_local_config()


class SignDictTestCase(unittest.TestCase):

    def test_can_sign_dict(self):
        _, fn = tempfile.mkstemp()
        self.addCleanup(os.remove, fn)

        key = RSA.generate(1024)
        with open(fn, 'wb') as fp:
            fp.write(key.exportKey())

        dict_ = {}
        message = SHA256.new(json.dumps(dict_).encode())
        result = utils.sign_dict(dict_, fn)

        signature = base64.b64decode(result)
        verifier = PKCS1_v1_5.new(key)
        is_valid = verifier.verify(message, signature)
        self.assertTrue(is_valid)

    def test_raises_error_if_invalid_file(self):
        with self.assertRaises(ValueError):
            utils.sign_dict({}, __file__)

        _, fn = tempfile.mkstemp()
        self.addCleanup(os.remove, fn)
        with self.assertRaises(ValueError):
            utils.sign_dict({}, fn)
