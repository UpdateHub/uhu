# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from efu.core.manager import InstallationSetMode
from efu.core.package import Package
from efu.exceptions import UploadError
from efu.utils import SERVER_URL_VAR

from utils import BasePushTestCase, HTTPTestCaseMixin

from . import PackageTestCase


class PushTestCase(BasePushTestCase):

    def test_upload_metadata_returns_None_when_successful(self):
        self.start_push_url(self.product, self.package_uid)
        self.package.objects.load()
        observed = self.package.upload_metadata()
        self.assertIsNone(observed)

    def test_upload_metadata_raises_exception_when_fail(self):
        self.start_push_url(self.product, self.package_uid, success=False)
        self.package.objects.load()
        with self.assertRaises(UploadError):
            self.package.upload_metadata()

    def test_upload_metadata_request_is_made_correctly(self):
        self.start_push_url(self.product, self.package_uid)
        start_url = self.httpd.url(
            '/products/{}/packages'.format(self.product))
        self.package.objects.load()
        self.package.upload_metadata()

        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        metadata = json.loads(request.body.decode())
        self.assertEqual(metadata, self.package.metadata())

    def test_upload_metadata_updates_package_uid(self):
        self.start_push_url(self.product, self.package_uid)
        self.package.objects.load()
        self.assertIsNone(self.package.uid)
        self.package.upload_metadata()
        self.assertEqual(self.package.uid, self.package_uid)

    def test_finish_push_returns_None_when_successful(self):
        self.package.uid = self.package_uid
        self.finish_push_url(self.product, self.package.uid)
        self.assertIsNone(self.package.finish_push())

    def test_finish_push_raises_error_when_fail(self):
        self.package.uid = self.package_uid
        self.finish_push_url(self.product, self.package_uid, success=False)
        with self.assertRaises(UploadError):
            self.package.finish_push()

    def test_finish_push_request_is_made_correctly(self):
        self.finish_push_url(self.product, self.package_uid, success=True)
        path = '/products/{}/packages/{}/finish'.format(
            self.product, self.package_uid)
        url = self.httpd.url(path)
        self.package.uid = self.package_uid
        self.package.finish_push()
        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

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


class PackageStatusTestCase(HTTPTestCaseMixin, PackageTestCase):

    def setUp(self):
        super().setUp()
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))

    def test_can_get_a_package_status(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.pkg_uid)
        package = Package(
            InstallationSetMode.Single, product=self.product, uid=self.pkg_uid)
        expected = 'finished'
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': expected}))
        observed = package.get_status()
        self.assertEqual(observed, expected)

    def test_get_package_status_raises_error_if_package_doesnt_exist(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.pkg_uid)
        self.httpd.register_response(path, status_code=404)
        package = Package(
            InstallationSetMode.Single, product=self.product, uid=self.pkg_uid)
        with self.assertRaises(ValueError):
            package.get_status()
