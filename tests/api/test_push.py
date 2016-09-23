# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from efu.core import Object, Package
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
        self.package = Package(version=self.version, product=self.product)
        for _ in range(3):
            fn = self.create_file('123')
            self.package.add_object(fn, 'raw', {'target-device': 'raw'})


class PushTestCase(BasePushTestCase):

    def test_start_push_returns_None_when_successful(self):
        self.set_push(self.product)
        self.package.load()
        push = Push(self.package)
        observed = push.start_push()
        self.assertIsNone(observed)

    def test_raises_exception_when_start_push_fails(self):
        self.set_push(self.product, start_success=False)
        self.package.load()
        push = Push(self.package)
        with self.assertRaises(exceptions.StartPushError):
            push.start_push()

    def test_start_push_request_is_made_correctly(self):
        self.set_push(self.product)
        start_url = self.httpd.url(
            '/products/{}/packages'.format(self.product))
        self.package.load()
        push = Push(self.package)
        push.start_push()

        request = self.httpd.requests[0]
        request_body = json.loads(request.body.decode())

        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(len(request_body.get('objects')), 3)
        self.assertEqual(request_body.get('version'), self.version)
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        # objects
        for obj in request_body.get('objects'):
            chunks = obj.get('chunks')
            self.assertIsNotNone(chunks)
            for chunk in chunks:
                self.assertIsNotNone(chunk.get('sha256sum'))
                self.assertIsNotNone(chunk.get('position'))
        # metadata
        metadata = request_body.get('metadata')
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['version'], self.version)
        self.assertEqual(metadata['product'], self.product)
        for metadata_obj in metadata['objects']:
            self.assertIsNotNone(metadata_obj['sha256sum'])
            self.assertIsNotNone(metadata_obj['filename'])
            self.assertIsNotNone(metadata_obj['size'])
            self.assertIsNotNone(metadata_obj['mode'])
            self.assertIsNotNone(metadata_obj['target-device'])

    def test_start_push_updates_finish_push_url(self):
        self.set_push(self.product)
        self.package.load()
        push = Push(self.package)
        push.start_push()
        self.assertIsNotNone(push.finish_push_url)

    def test_finish_push_returns_None_when_successful(self):
        push = Push(self.package)
        push.finish_push_url = self.finish_push_url(success=True)
        observed = push.finish_push()
        self.assertIsNone(observed)

    def test_finish_push_raises_exception_when_fail(self):
        push = Push(self.package)
        push.finish_push_url = self.finish_push_url(success=False)
        with self.assertRaises(exceptions.FinishPushError):
            push.finish_push()

    def test_finish_push_request_is_made_correctly(self):
        url = self.finish_push_url(success=True)
        push = Push(self.package)
        push.finish_push_url = url
        push.finish_push()
        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_upload_objects_return_None_when_successful(self):
        uploads = self.create_package_uploads(self.package)
        self.set_push(self.product, uploads=uploads)
        push = Push(self.package)
        push.start_push()
        observed = push.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_return_None_when_file_exists(self):
        uploads = self.create_package_uploads(self.package, obj_exists=True)
        self.set_push(self.product, uploads=uploads)
        push = Push(self.package)
        push.start_push()
        observed = push.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_raises_exception_when_upload_part_fails(self):
        uploads = self.create_package_uploads(self.package, success=False)
        self.set_push(self.product, uploads=uploads)

        push = Push(self.package)
        push.start_push()
        with self.assertRaises(exceptions.UploadError):
            push.upload_objects()

    def test_upload_objects_requests_are_made_correctly(self):
        uploads = self.create_package_uploads(self.package)
        self.set_push(self.product, uploads=uploads)
        push = Push(self.package)
        push.start_push()
        push.upload_objects()
        # 1 request for starting push
        # 9 requests since 3 files must be uploaded in 3 chunks each
        # Total: 10 requests
        self.assertEqual(len(self.httpd.requests), 10)
