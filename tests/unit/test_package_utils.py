# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest

from efu.core.utils import (
    create_package_file, create_package_from_metadata,
    load_package, write_package, add_image, remove_image)
from efu.core.parser_utils import InstallMode

from ..base import ObjectMockMixin, BaseTestCase


class UtilsTestCase(ObjectMockMixin, BaseTestCase):

    def setUp(self):
        self.addCleanup(self.remove_file, '.efu')

    def test_can_load_package(self):
        create_package_file(product='1234X')
        package = load_package()
        self.assertEqual(package['product'], '1234X')

    def test_load_package_raises_error_if_package_does_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            load_package()

    def test_can_write_package(self):
        write_package({'product': '1234'})
        with open('.efu') as fp:
            package = json.load(fp)
        self.assertEqual(package.get('product'), '1234')

    def test_can_create_package_file(self):
        create_package_file(product='1234X')
        self.assertTrue(os.path.exists('.efu'))
        with open('.efu') as fp:
            data = json.load(fp)
        self.assertEqual(data['product'], '1234X')

    def test_do_not_create_package_file_if_it_exists(self):
        with open('.efu', 'w'):
            pass
        with self.assertRaises(FileExistsError):
            create_package_file(product='1234X')

    def test_add_image_raises_error_if_package_file_does_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            add_image('file.py', {})

    def test_can_add_image_within_package_file(self):
        create_package_file(product='1234X')
        options = {
            'install-mode': 'raw',
            'target-device': 'device'
        }
        add_image(filename='spam.py', options=options)

        with open('.efu') as fp:
            data = json.load(fp)
        objects = data.get('objects')

        self.assertIsNotNone(objects)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects['spam.py']['install-mode'], 'raw')
        self.assertEqual(objects['spam.py']['target-device'], 'device')

    def test_can_update_a_image(self):
        create_package_file(product='1234X')
        options = {
            'install-mode': 'raw',
            'target-device': 'device-a'
        }
        add_image(filename='spam.py', options=options)

        options = {
            'install-mode': 'raw',
            'target-device': 'device-b'
        }
        add_image(filename='spam.py', options=options)

        with open('.efu') as fp:
            data = json.load(fp)
        objects = data.get('objects')

        self.assertEqual(len(objects), 1)
        self.assertEqual(objects['spam.py']['install-mode'], 'raw')
        self.assertEqual(objects['spam.py']['target-device'], 'device-b')

    def test_can_remove_an_image(self):
        create_package_file(product='1234X')
        options = {'install_mode': 'raw', 'target-device': 'device-a'}

        add_image(filename='spam.py', options=options)
        with open('.efu') as fp:
            package = json.load(fp)
        self.assertIsNotNone(package['objects']['spam.py'])
        self.assertEqual(len(package['objects']), 1)

        remove_image('spam.py')
        with open('.efu') as fp:
            package = json.load(fp)
        self.assertIsNone(package['objects'].get('spam.py'))
        self.assertEqual(len(package['objects']), 0)

    def test_remove_image_raises_error_when_image_does_not_exist(self):
        create_package_file(product='1234X')
        with self.assertRaises(KeyError):
            remove_image('spam.py')

    def test_can_create_package_file_from_metadata(self):
        expected = {
            'product': 'cfe2be1c64b0387500853de0f48303e3de7b1c6f1508dc719eeafa0d41c36722',  # nopep8
            'objects': [
                {
                    'install-mode': 'copy',
                    'filename': 'etc/passwd',
                    'filesystem': 'btrfs',
                    'target-device': '/dev/sda',
                    'target-path': '/etc/passwd',
                    'format?': True,
                    'format-options': '-a',
                    'mount-options': '-b'
                },
                {
                    'install-mode': 'tarball',
                    'filename': 'etc/hostname',
                    'filesystem': 'ext4',
                    'target-device': '/dev/sda',
                    'target-path': '/etc/hostname'
                },
                {
                    'install-mode': 'raw',
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
        self.assertFalse(os.path.exists('.efu'))

        observed = create_package_from_metadata(metadata)

        self.assertEqual(observed, expected)

        self.assertTrue(os.path.exists('.efu'))
        with open('.efu') as fp:
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
        with open('.efu', 'w') as fp:
            json.dump({'package': '1234', 'version': '2.0'}, fp)
        with open('tests/unit/fixtures/metadata.json') as fp:
            metadata = json.load(fp)
        with self.assertRaises(FileExistsError):
            create_package_from_metadata(metadata)
