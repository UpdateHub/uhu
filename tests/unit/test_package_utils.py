# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest

from efu.utils import LOCAL_CONFIG_VAR
from efu.core.utils import (
    create_package_from_metadata, load_package, write_package)

from ..base import PackageMockMixin, BaseTestCase, delete_environment_variable


class UtilsTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.pkg_file = self.create_file(json.dumps({
            'product': self.product
        }).encode())
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.addCleanup(delete_environment_variable, LOCAL_CONFIG_VAR)

    def test_can_load_package(self):
        package = load_package()
        self.assertEqual(package['product'], self.product)

    def test_load_package_raises_error_if_package_does_not_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = 'no-exists'
        with self.assertRaises(FileNotFoundError):
            load_package()

    def test_can_write_package(self):
        write_package({'product': '1234'})
        with open(self.pkg_file) as fp:
            package = json.load(fp)
        self.assertEqual(package.get('product'), '1234')

    def test_can_create_package_file_from_metadata(self):
        os.remove(self.pkg_file)
        expected = {
            'product': 'cfe2be1c64b0387500853de0f48303e3de7b1c6f1508dc719eeafa0d41c36722',  # nopep8
            'objects': [
                {
                    'mode': 'copy',
                    'filename': 'etc/passwd',
                    'filesystem': 'btrfs',
                    'target-device': '/dev/sda',
                    'target-path': '/etc/passwd',
                    'format?': True,
                    'format-options': '-a',
                    'mount-options': '-b'
                },
                {
                    'mode': 'tarball',
                    'filename': 'etc/hostname',
                    'filesystem': 'ext4',
                    'target-device': '/dev/sda',
                    'target-path': '/etc/hostname'
                },
                {
                    'mode': 'raw',
                    'filename': 'boot',
                    'target-device': '/dev/sda1',
                    'truncate': False,
                    'count': 1024,
                    'seek': 512,
                    'skip': 256,
                    'chunk-size': 128
                }
            ]
        }
        with open('tests/unit/fixtures/metadata.json') as fp:
            metadata = json.load(fp)
        self.assertFalse(os.path.exists(self.pkg_file))

        observed = create_package_from_metadata(metadata)

        self.assertEqual(observed, expected)

        self.assertTrue(os.path.exists(self.pkg_file))
        with open(self.pkg_file) as fp:
            package = json.load(fp)
        self.assertEqual(package, expected)

    def test_metadata_isnt_changed_after_package_creation_from_metadata(self):
        fp = open('tests/unit/fixtures/metadata.json')
        observed = json.load(fp)
        create_package_from_metadata(observed)
        fp.seek(0)
        expected = json.load(fp)
        self.assertEqual(observed, expected)

    def test_create_package_from_metadata_raises_error_if_package_exists(self):
        with open(self.pkg_file, 'w') as fp:
            json.dump({'package': '1234', 'version': '2.0'}, fp)
        with open('tests/unit/fixtures/metadata.json') as fp:
            metadata = json.load(fp)
        with self.assertRaises(FileExistsError):
            create_package_from_metadata(metadata)
