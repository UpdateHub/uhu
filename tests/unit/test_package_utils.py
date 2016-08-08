# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest

from efu.package.exceptions import DotEfuExistsError, DotEfuDoesNotExistError
from efu.package.utils import (
    create_efu_file, add_image, load_package, write_package)
from efu.package.parser_utils import InstallMode


class UtilsTestCase(unittest.TestCase):

    def remove_efu_file_cleanup(self):
        try:
            os.remove('.efu')
        except:
            # file already deleted
            pass

    def setUp(self):
        self.addCleanup(self.remove_efu_file_cleanup)

    def test_can_load_package(self):
        create_efu_file(product='1234X', version='2.0')
        package = load_package()
        self.assertEqual(package['product'], '1234X')
        self.assertEqual(package['version'], '2.0')

    def test_load_package_raises_error_if_package_does_not_exist(self):
        with self.assertRaises(DotEfuDoesNotExistError):
            load_package()

    def test_can_write_package(self):
        write_package({'product': '1234', 'version': '2.0'})
        with open('.efu') as fp:
            package = json.load(fp)
        self.assertEqual(package.get('product'), '1234')
        self.assertEqual(package.get('version'), '2.0')

    def test_can_create_efu_file(self):
        create_efu_file(product='1234X', version='2.0')
        self.assertTrue(os.path.exists('.efu'))
        with open('.efu') as fp:
            data = json.load(fp)
        self.assertEqual(data['product'], '1234X')
        self.assertEqual(data['version'], '2.0')

    def test_do_not_create_efu_file_if_it_exists(self):
        with open('.efu', 'w'):
            pass
        with self.assertRaises(DotEfuExistsError):
            create_efu_file(product='1234X', version='2.0')

    def test_add_image_raises_error_if_dot_efu_does_not_exist(self):
        with self.assertRaises(DotEfuDoesNotExistError):
            add_image('file.py', {})

    def test_can_add_image_within_dot_efu_file(self):
        create_efu_file(product='1234X', version='2.0')
        mode = InstallMode('raw')
        options = {
            'install_mode': mode,
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
        create_efu_file(product='1234X', version='2.0')
        mode = InstallMode('raw')
        options = {
            'install_mode': mode,
            'target-device': 'device-a'
        }
        add_image(filename='spam.py', options=options)

        options = {
            'install_mode': mode,
            'target-device': 'device-b'
        }
        add_image(filename='spam.py', options=options)

        with open('.efu') as fp:
            data = json.load(fp)
        files = data.get('files')

        self.assertEqual(len(files), 1)
        self.assertEqual(files['spam.py']['install-mode'], 'raw')
        self.assertEqual(files['spam.py']['target-device'], 'device-b')
