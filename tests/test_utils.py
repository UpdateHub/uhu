# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
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


class StrinUtilsTestCase(unittest.TestCase):

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


class CompressedObjectTestCase(FileFixtureMixin, UHUTestCase):

    def setUp(self):
        self.fixtures_dir = 'tests/fixtures/compressed/'
        uncompressed_fn = os.path.join(self.fixtures_dir, 'base.txt')
        self.size = os.path.getsize(uncompressed_fn)

    def test_can_get_gzip_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.gz')
        observed = utils.get_uncompressed_size(fn, 'gzip')
        self.assertEqual(observed, self.size)

    def test_can_get_xz_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.xz')
        observed = utils.get_uncompressed_size(fn, 'xz')
        self.assertEqual(observed, self.size)

    def test_can_get_lzo_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        observed = utils.get_uncompressed_size(fn, 'lzop')
        self.assertEqual(observed, self.size)

    def test_can_get_tar_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar.gz')
        observed = utils.get_uncompressed_size(fn, 'gzip')
        expected = os.path.getsize(
            os.path.join(self.fixtures_dir, 'archive.tar'))
        self.assertEqual(observed, expected)

    def test_can_get_symbolic_link_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'symbolic.gz')
        observed = utils.get_uncompressed_size(fn, 'gzip')
        self.assertEqual(observed, self.size)

    def test_uncompressed_size_raises_error_if_not_supported_by_uhu(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.bz2')
        with self.assertRaises(ValueError):
            utils.get_uncompressed_size(fn, 'bz2')

    @patch('uhu.utils.shutil.which', return_value=None)
    def test_uncompressed_size_raises_error_if_not_supported_by_os(self, _):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        with self.assertRaises(SystemError):
            utils.get_uncompressed_size(fn, 'lzop')

    @patch('uhu.utils.subprocess.check_call', return_value=1)
    def test_uncompressed_size_raises_error_if_corrupted_file(self, _):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        with self.assertRaises(ValueError):
            utils.get_uncompressed_size(fn, 'lzop')

    def test_can_get_gzip_compressor_format_from_file(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.gz')
        observed = utils.get_compressor_format(fn)
        self.assertEqual(observed, 'gzip')

    def test_can_get_lzo_compressor_format_from_file(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        observed = utils.get_compressor_format(fn)
        self.assertEqual(observed, 'lzop')

    def test_can_get_xz_compressor_format_from_file(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.xz')
        observed = utils.get_compressor_format(fn)
        self.assertEqual(observed, 'xz')

    def test_can_get_compressor_format_from_symbolic_link(self):
        fn = os.path.join(self.fixtures_dir, 'symbolic.gz')
        observed = utils.get_compressor_format(fn)
        self.assertEqual(observed, 'gzip')

    def test_get_compressor_format_returns_None_if_not_supported_by_uhu(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.bz2')
        self.assertIsNone(utils.get_compressor_format(fn))

    def test_is_valid_compressed_file_returns_false_if_invalid(self):
        # Here we try to check a bz2 with a gzip compressor
        fn = os.path.join(self.fixtures_dir, 'base.txt.bz2')
        self.assertFalse(utils.is_valid_compressed_file(fn, 'gzip'))
