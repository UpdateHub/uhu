# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from efu.push import exceptions
from efu.core import File, Package
from efu.push.push import Push, PushExitCode

from ..base import EFUTestCase


class PushTestCase(EFUTestCase):

    def test_start_push_returns_NONE_when_successful(self):
        self.set_push(self.product_id)
        push = Push(self.package)
        observed = push._start_push()
        self.assertIsNone(observed)

    def test_raises_exception_when_start_push_fails(self):
        self.set_push(self.product_id, start_success=False)
        push = Push(self.package)
        with self.assertRaises(exceptions.StartPushError):
            push._start_push()

    def test_start_push_request_is_made_correctly(self):
        self.set_push(self.product_id)
        start_url = self.httpd.url(
            '/products/{}/commits'.format(self.product_id))

        push = Push(self.package)
        push._start_push()

        request = self.httpd.requests[0]
        request_body = json.loads(request.body.decode())

        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(len(request_body.get('objects')), 3)
        self.assertEqual(request_body.get('version'), self.version)
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        # objects
        for file in request_body.get('objects'):
            self.assertIsNotNone(file.get('id'))
            self.assertIsNotNone(file.get('sha256sum'))
            self.assertIsNotNone(file.get('parts'))
            for part in file.get('parts'):
                self.assertIsNotNone(part.get('sha256sum'))
                self.assertIsNotNone(part.get('number'))
        # metadata
        metadata = request_body.get('metadata')
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['version'], self.version)
        self.assertEqual(metadata['product'], self.product_id)
        for image in metadata['images']:
            self.assertIsNotNone(image['sha256sum'])
            self.assertIsNotNone(image['filename'])
            self.assertIsNotNone(image['size'])
            self.assertIsNotNone(image['install-mode'])
            self.assertIsNotNone(image['target-device'])

    def test_start_push_updates_finish_push_url(self):
        self.set_push(self.product_id)
        push = Push(self.package)
        push._start_push()
        self.assertIsNotNone(push._finish_push_url)

    def test_finish_push_returns_NONE_when_successful(self):
        push = Push(self.package)
        push._finish_push_url = self.finish_push_url(success=True)
        observed = push._finish_push()
        self.assertIsNone(observed)

    def test_finish_push_raises_exception_when_fail(self):
        push = Push(self.package)
        push._finish_push_url = self.finish_push_url(success=False)
        with self.assertRaises(exceptions.FinishPushError):
            push._finish_push()

    def test_finish_push_request_is_made_correctly(self):
        url = self.finish_push_url(success=True)
        push = Push(self.package)
        push._finish_push_url = url
        push._finish_push()
        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_upload_files_return_NONE_when_successful(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product_id, uploads=uploads)
        push = Push(self.package)
        push._start_push()
        observed = push._upload_files()
        self.assertIsNone(observed)

    def test_upload_files_return_NONE_when_file_exists(self):
        uploads = self.create_uploads_meta(self.files, file_exists=True)
        self.set_push(self.product_id, uploads=uploads)
        push = Push(self.package)
        push._start_push()
        observed = push._upload_files()
        self.assertIsNone(observed)

    def test_upload_files_raises_exception_when_upload_part_fails(self):
        uploads = self.create_uploads_meta(self.files, success=False)
        self.set_push(self.product_id, uploads=uploads)

        push = Push(self.package)
        push._start_push()
        with self.assertRaises(exceptions.FileUploadError):
            push._upload_files()

    def test_upload_files_requests_are_made_correctly(self):
        fns = [self.create_file(b'000') for i in range(3)]
        pkg_fn = self.create_package_file(self.product_id, fns)
        os.environ['EFU_PACKAGE_FILE'] = pkg_fn
        pkg = Package(self.version)
        files = list(pkg.files.values())
        File._File__reset_id_generator()
        uploads = self.create_uploads_meta(files[:2])
        uploads.append(self.create_upload_meta(files[-1], file_exists=True))
        self.set_push(self.product_id, uploads=uploads)

        push = Push(pkg)
        push._start_push()
        push._upload_files()
        # 1 request for starting push
        # 6 requests since 2 files must be uploaded in 3 chunks each
        # Total: 7 requests
        total_requests = 7
        self.assertEqual(len(self.httpd.requests), total_requests)

    def test_push_run_returns_SUCCESS_when_successful(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product_id, uploads=uploads)
        push = Push(self.package)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.SUCCESS)

    def test_push_run_returns_START_FAIL_when_fail_on_start(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(
            self.product_id, uploads=uploads, start_success=False)
        push = Push(self.package)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.START_FAIL)

    def test_push_run_returns_UPLOAD_FAIL_when_part_fail(self):
        uploads = self.create_uploads_meta(self.files, success=False)
        self.set_push(self.product_id, uploads=uploads)
        push = Push(self.package)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.UPLOAD_FAIL)

    def test_push_run_returns_FINISH_FAIL_when_fail_on_finish(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(
            self.product_id, uploads=uploads, finish_success=False)
        push = Push(self.package)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.FINISH_FAIL)
