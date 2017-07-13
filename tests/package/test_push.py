# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
from unittest.mock import patch

from uhu.core.package import Package
from uhu.core.updatehub import get_package_status
from uhu.exceptions import UploadError
from uhu.utils import SERVER_URL_VAR

from utils import BasePushTestCase, HTTPTestCaseMixin

from . import PackageTestCase


class PushTestCase(BasePushTestCase):

    def test_upload_metadata_updates_package_uid_when_successful(self):
        self.start_push_url(self.package_uid)
        self.package.objects.load()
        self.assertIsNone(self.package.uid)
        self.package.upload_metadata()
        self.assertEqual(self.package.uid, self.package_uid)

    def test_upload_metadata_raises_exception_when_fail(self):
        self.start_push_url(self.package_uid, success=False)
        self.package.objects.load()
        with self.assertRaises(UploadError):
            self.package.upload_metadata()

    @patch('uhu.core.updatehub.http')
    def test_upload_metadata_raises_error_when_unathorized(self, mock):
        mock.post.return_value.status_code = 401
        with self.assertRaises(UploadError):
            self.package.upload_metadata()

    def test_upload_metadata_request_is_made_correctly(self):
        self.start_push_url(self.package_uid)
        start_url = self.httpd.url('/packages')
        self.package.objects.load()
        self.package.upload_metadata()

        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        metadata = json.loads(request.body.decode())
        self.assertEqual(metadata, self.package.to_metadata())

    def test_upload_objects_return_None_when_successful(self):
        self.set_push(self.package, self.package_uid)
        self.package.upload_metadata()
        observed = self.package.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_return_None_when_file_exists(self):
        self.set_push(self.package, self.package_uid, upload_exists=True)
        self.package.upload_metadata()
        observed = self.package.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_raises_error_when_upload_fails(self):
        self.set_push(self.package, self.package_uid, upload_success=False)
        self.package.upload_metadata()
        with self.assertRaises(UploadError):
            self.package.upload_objects()

    def test_upload_objects_requests_are_made_correctly(self):
        self.set_push(self.package, self.package_uid)
        self.package.upload_metadata()
        self.package.upload_objects()
        self.package.finish_push()
        # 1 request for starting push
        # 3 * (2 requests per file [get url and upload])
        # 1 request for finishing push
        # Total: 8 requests
        self.assertEqual(len(self.httpd.requests), 8)

    def test_finish_push_returns_None_when_successful(self):
        self.package.uid = self.package_uid
        self.finish_push_url(self.package.uid)
        self.assertIsNone(self.package.finish_push())

    def test_finish_push_raises_error_when_fail(self):
        self.package.uid = self.package_uid
        self.finish_push_url(self.package_uid, success=False)
        with self.assertRaises(UploadError):
            self.package.finish_push()

    def test_push_returns_None_when_successful(self):
        self.set_push(self.package, self.package_uid)
        self.assertIsNone(self.package.push())

    def test_finish_push_request_is_made_correctly(self):
        self.finish_push_url(self.package_uid, success=True)
        path = '/packages/{}/finish'.format(self.package_uid)
        url = self.httpd.url(path)
        self.package.uid = self.package_uid
        self.package.finish_push()
        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'PUT')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')


class PackageStatusTestCase(HTTPTestCaseMixin, PackageTestCase):

    def setUp(self):
        super().setUp()
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))

    def test_can_get_package_status(self):
        path = '/packages/{}'.format(self.pkg_uid)
        expected = 'finished'
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': expected}))
        observed = get_package_status(self.pkg_uid)
        self.assertEqual(observed, expected)

    def test_get_package_status_raises_error_if_package_doesnt_exist(self):
        path = '/packages/{}'.format(self.pkg_uid)
        self.httpd.register_response(path, status_code=404)
        with self.assertRaises(ValueError):
            get_package_status(self.pkg_uid)
