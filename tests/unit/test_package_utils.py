# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest

from efu.core.exceptions import (
    PackageObjectExistsError, PackageObjectDoesNotExistError,
    ObjectDoesNotExistError
)
from efu.core.utils import (
    create_package_file, remove_package_file, copy_package_file,
    add_image, remove_image, list_images,
    load_package, write_package,
    create_package_from_metadata, is_metadata_valid,
    yes_or_no
)
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
        with self.assertRaises(PackageObjectDoesNotExistError):
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
        with self.assertRaises(PackageObjectExistsError):
            create_package_file(product='1234X')

    def test_add_image_raises_error_if_package_file_does_not_exist(self):
        with self.assertRaises(PackageObjectDoesNotExistError):
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
        files = data.get('files')

        self.assertIsNotNone(files)
        self.assertEqual(len(files), 1)
        self.assertEqual(files['spam.py']['install-mode'], 'raw')
        self.assertEqual(files['spam.py']['target-device'], 'device')

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
        files = data.get('files')

        self.assertEqual(len(files), 1)
        self.assertEqual(files['spam.py']['install-mode'], 'raw')
        self.assertEqual(files['spam.py']['target-device'], 'device-b')

    def test_can_remove_an_image(self):
        create_package_file(product='1234X')
        options = {'install_mode': 'raw', 'target-device': 'device-a'}

        add_image(filename='spam.py', options=options)
        with open('.efu') as fp:
            package = json.load(fp)
        self.assertIsNotNone(package['files']['spam.py'])
        self.assertEqual(len(package['files']), 1)

        remove_image('spam.py')
        with open('.efu') as fp:
            package = json.load(fp)
        self.assertIsNone(package['files'].get('spam.py'))
        self.assertEqual(len(package['files']), 0)

    def test_remove_image_raises_error_when_image_does_not_exist(self):
        create_package_file(product='1234X')
        with self.assertRaises(ObjectDoesNotExistError):
            remove_image('spam.py')

    def test_can_remove_package_file(self):
        with open('.efu', 'w') as fp:
            pass
        self.assertTrue(os.path.exists('.efu'))
        remove_package_file()
        self.assertFalse(os.path.exists('.efu'))

    def test_remove_package_file_raises_error_when_file_already_deleted(self):
        self.assertFalse(os.path.exists('.efu'))
        with self.assertRaises(PackageObjectDoesNotExistError):
            remove_package_file()

    def test_list_images_returns_NONE_if_successful(self):
        package = {
            'product': '1',
            'files': {
                'spam.py': {
                    'install-mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        with open('.efu', 'w') as fp:
            json.dump(package, fp)
        observed = list_images()
        self.assertIsNone(observed)

    def test_list_images_raises_error_if_package_does_not_exist(self):
        with self.assertRaises(PackageObjectDoesNotExistError):
            list_images()

    def test_can_export_package_file(self):
        self.addCleanup(self.remove_file, 'exported')
        expected = {
            'product': '1',
            'files': {
                'spam.py': {
                    'install-mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        with open('.efu', 'w') as fp:
            json.dump(expected, fp)

        copy_package_file('exported')

        with open('exported') as fp:
            observed = json.load(fp)
        self.assertEqual(observed, expected)

    def test_copy_package_file_raises_error_if_package_doesnt_exist(self):
        with self.assertRaises(PackageObjectDoesNotExistError):
            copy_package_file('exported')
        self.assertFalse(os.path.exists('exported'))

    def test_can_create_package_file_from_metadata(self):
        expected = {
            'product': 'cfe2be1c64b0387500853de0f48303e3de7b1c6f1508dc719eeafa0d41c36722',  # nopep8
            'files': [
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
        with self.assertRaises(PackageObjectExistsError):
            create_package_from_metadata(metadata)

    def test_is_valid_metadata_returns_TRUE_if_valid_document(self):
        with open('tests/unit/fixtures/metadata.json') as fp:
            metadata = json.load(fp)
        self.assertTrue(is_metadata_valid(metadata))

    def test_is_valid_metadata_returns_FALSE_if_invalid_document(self):
        metadata = {}
        self.assertFalse(is_metadata_valid(metadata))

    def test_yes_or_no_returns_yes_if_TRUE(self):
        expected = 'yes'
        observed = yes_or_no(True)
        self.assertEqual(observed, expected)

    def test_yes_or_no_returns_no_if_FALSE(self):
        expected = 'no'
        observed = yes_or_no(False)
        self.assertEqual(observed, expected)
