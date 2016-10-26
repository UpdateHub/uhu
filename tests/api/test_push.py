# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from efu.core import Package
from efu.transactions import exceptions
from efu.transactions.push import Push
from efu.utils import SERVER_URL_VAR, CHUNK_SIZE_VAR

from ..utils import (
    HTTPTestCaseMixin, EFUTestCase, EnvironmentFixtureMixin, FileFixtureMixin,
    PushFixtureMixin, UploadFixtureMixin)


class BasePushTestCase(
        PushFixtureMixin, UploadFixtureMixin, EnvironmentFixtureMixin,
        FileFixtureMixin, HTTPTestCaseMixin, EFUTestCase):

    def setUp(self):
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        self.product = '0' * 64
        self.version = '2.0'
        self.package_uid = '1' * 64
        self.package = Package(version=self.version, product=self.product)
        self.package.objects.add_list()
        for _ in range(3):
            fn = self.create_file('123')
            self.package.objects.add(
                0, fn, 'raw', {'target-device': '/dev/sda'})


class PushTestCase(BasePushTestCase):

    def test_start_push_returns_None_when_successful(self):
        self.start_push_url(self.product, self.package_uid)
        self.package.load()
        push = Push(self.package)
        observed = push.start_push()
        self.assertIsNone(observed)

    def test_start_push_raises_exception_when_fail(self):
        self.start_push_url(self.product, self.package_uid, success=False)
        self.package.load()
        push = Push(self.package)
        with self.assertRaises(exceptions.StartPushError):
            push.start_push()

    def test_start_push_request_is_made_correctly(self):
        self.start_push_url(self.product, self.package_uid)
        start_url = self.httpd.url(
            '/products/{}/packages'.format(self.product))
        self.package.load()
        push = Push(self.package)
        push.start_push()

        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        metadata = json.loads(request.body.decode())
        self.assertEqual(metadata, self.package.metadata())

    def test_start_push_updates_package_uid(self):
        self.start_push_url(self.product, self.package_uid)
        self.package.load()
        push = Push(self.package)
        self.assertIsNone(self.package.uid)
        push.start_push()
        self.assertEqual(self.package.uid, self.package_uid)

    def test_finish_push_returns_None_when_successful(self):
        push = Push(self.package)
        self.package.uid = self.package_uid
        self.finish_push_url(self.product, self.package.uid)
        self.assertIsNone(push.finish_push())

    def test_finish_push_raises_error_when_fail(self):
        push = Push(self.package)
        self.package.uid = self.package_uid
        self.finish_push_url(self.product, self.package_uid, success=False)
        with self.assertRaises(exceptions.FinishPushError):
            push.finish_push()

    def test_finish_push_request_is_made_correctly(self):
        self.finish_push_url(self.product, self.package_uid, success=True)
        path = '/products/{}/packages/{}/finish'.format(
            self.product, self.package_uid)
        url = self.httpd.url(path)
        push = Push(self.package)
        self.package.uid = self.package_uid
        push.finish_push()
        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_upload_objects_return_None_when_successful(self):
        self.set_push(self.package, self.package_uid)
        push = Push(self.package)
        push.start_push()
        observed = push.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_return_None_when_file_exists(self):
        self.set_push(self.package, self.package_uid, upload_exists=True)
        push = Push(self.package)
        push.start_push()
        observed = push.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_requests_are_made_correctly(self):
        self.set_push(self.package, self.package_uid)
        push = Push(self.package)
        push.start_push()
        push.upload_objects()
        push.finish_push()
        # 1 request for starting push
        # 3 * (2 requests per file [get url and upload])
        # 1 request for finishing push
        # Total: 8 requests
        self.assertEqual(len(self.httpd.requests), 8)
