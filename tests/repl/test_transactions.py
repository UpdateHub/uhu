# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import copy
import json
import os
from unittest.mock import Mock, patch

from uhu.repl.repl import UHURepl
from uhu.repl import functions
from uhu.utils import SERVER_URL_VAR

from utils import (
    HTTPTestCaseMixin, UHUTestCase, EnvironmentFixtureMixin,
    BasePullTestCase, BasePushTestCase)


class PackageStatusTestCase(
        EnvironmentFixtureMixin, HTTPTestCaseMixin, UHUTestCase):

    def setUp(self):
        self.repl = UHURepl()
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        self.product = '1' * 64
        self.pkg_uid = '1'

    def test_can_get_package_status(self):
        path = '/packages/{}'.format(self.pkg_uid)
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': 'success'}))

        builtins = copy.deepcopy(functions.__builtins__)
        builtins['print'] = Mock()
        with patch.dict(functions.__builtins__, builtins):
            self.repl.package.product = self.product
            self.repl.arg = self.pkg_uid
            functions.get_package_status(self.repl)
            functions.__builtins__['print'].assert_called_once_with('success')

    def test_get_package_status_raises_error_if_missing_product(self):
        self.assertIsNone(self.repl.package.product)
        with self.assertRaises(ValueError):
            functions.get_package_status(self.repl)

    def test_get_package_status_raises_error_if_missing_package_uid(self):
        self.repl.package.product = '1'
        self.assertIsNone(self.repl.arg)
        with self.assertRaises(ValueError):
            functions.get_package_status(self.repl)


class PushTestCase(BasePushTestCase):

    def setUp(self):
        super().setUp()
        self.repl = UHURepl()

    def test_can_push_package(self):
        self.repl.package.objects.create('raw', {
            'filename': __file__,
            'target-type': 'device',
            'target': '/',
        })
        self.repl.package.product = self.product
        self.repl.package.version = '2.0'
        self.set_push(self.repl.package, '100')
        self.assertIsNone(self.repl.package.uid)
        functions.push_package(self.repl)
        self.assertEqual(self.repl.package.uid, '100')

    def test_push_raises_error_if_missing_product(self):
        self.repl.package.version = '2.0'
        with self.assertRaises(ValueError):
            functions.push_package(self.repl)

    def test_push_raises_error_if_missing_version(self):
        self.repl.package.product = self.product
        with self.assertRaises(ValueError):
            functions.push_package(self.repl)


class PullTestCase(BasePullTestCase):

    def setUp(self):
        super().setUp()
        self.repl = UHURepl()

    @patch('uhu.repl.helpers.prompt')
    def test_can_download_package_fully(self, prompt):
        prompt.side_effect = [self.pkg_uid, 'yes']
        self.assertIsNone(self.repl.package.product)
        functions.pull_package(self.repl)
        print(os.getcwd())
        print(os.listdir())
        self.assertTrue(os.path.exists(self.pkg_fn))
        self.assertEqual(self.repl.package.product, self.product)
        self.assertTrue(os.path.exists(self.obj_fn))

    @patch('uhu.repl.helpers.prompt')
    def test_can_download_only_metadata_package(self, prompt):
        prompt.side_effect = [self.pkg_uid, 'no']
        self.assertIsNone(self.repl.package.product)
        functions.pull_package(self.repl)
        print(os.getcwd())
        print(os.listdir())
        self.assertTrue(os.path.exists(self.pkg_fn))
        self.assertFalse(os.path.exists(self.obj_fn))
        self.assertEqual(self.repl.package.product, self.product)
