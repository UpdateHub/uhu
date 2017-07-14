# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import copy
import json
import os
import unittest
from unittest.mock import Mock, patch

from uhu.repl.repl import UHURepl
from uhu.repl import functions
from uhu.utils import SERVER_URL_VAR

from utils import HTTPTestCaseMixin, UHUTestCase, EnvironmentFixtureMixin


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
            functions.package_status(self.repl)
            functions.__builtins__['print'].assert_called_once_with('success')

    def test_raises_error_if_missing_product(self):
        self.assertIsNone(self.repl.package.product)
        with self.assertRaises(ValueError):
            functions.package_status(self.repl)

    def test_raises_error_if_missing_package_uid(self):
        self.repl.package.product = '1'
        self.assertIsNone(self.repl.arg)
        with self.assertRaises(ValueError):
            functions.package_status(self.repl)


class PushPackageTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.repl = UHURepl()

    def test_can_push_package(self):
        ctx = Mock()
        ctx.package.push.return_value = '100'
        ctx.package.uid = None
        functions.push_package(ctx)
        self.assertEqual(ctx.package.uid, '100')

    def test_raises_error_if_missing_product(self):
        self.repl.package.version = '2.0'
        with self.assertRaises(ValueError):
            functions.push_package(self.repl)

    def test_raises_error_if_missing_version(self):
        self.repl.package.product = 'product'
        with self.assertRaises(ValueError):
            functions.push_package(self.repl)
