# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os

from efu.push import exceptions
from efu.push.push import Push, PushExitCode

from ..base import BasePushTestCase


class PushTestCase(BasePushTestCase):

    def setUp(self):
        super().setUp()
        self.product_id = 'P1234'
        base_files = [
            self.fixture.set_file(self.product_id, 0, exists=True),
            self.fixture.set_file(self.product_id, 1, exists=False),
        ]
        self.files, self.responses = [], []
        for file, response in base_files:
            self.files.append(file)
            self.responses.append(response)
        self.package_fn = self.fixture.set_package(self.product_id, self.files)

    def test_can_make_initial_payload_correctly(self):
        product_id = 123
        files, hashes = [], []
        for content in (b'spam', b'eggs'):
            files.append(self.fixture.create_file(content))
            hashes.append(hashlib.sha256(content).hexdigest())

        pkg = self.fixture.set_package(product_id, files)
        push = Push(pkg)
        payload = json.loads(push._initial_payload)

        self.assertEqual(payload['product_id'], product_id)
        self.assertEqual(len(payload['files']), len(files))
        for observed, expected in zip(payload['files'], hashes):
            self.assertEqual(observed['sha256'], expected)

    def test_can_retrieve_host_url_by_hardcode(self):
        del os.environ['EFU_SERVER_URL']
        push = Push(self.package_fn)
        expected = 'http://0.0.0.0/product/P1234/upload/'
        observed = push._start_push_url
        self.assertEqual(observed, expected)

    def test_can_retrieve_host_url_by_environment_variable(self):
        os.environ['EFU_SERVER_URL'] = 'http://spam.eggs.com'
        push = Push(self.package_fn)
        expected = 'http://spam.eggs.com/product/P1234/upload/'
        observed = push._start_push_url
        self.assertEqual(observed, expected)

    def test_start_push_returns_NONE_when_successful(self):
        self.fixture.register_start_push_url(
            self.product_id, self.responses)
        push = Push(self.package_fn)
        observed = push._start_push()
        self.assertIsNone(observed)

    def test_start_push_raises_exception_when_fail(self):
        self.fixture.register_start_push_url(
            self.product_id, self.files, start_success=False)
        push = Push(self.package_fn)
        with self.assertRaises(exceptions.StartPushError):
            push._start_push()

    def test_start_push_request_is_made_correctly(self):
        start_url, _ = self.fixture.register_start_push_url(
            self.product_id, self.responses)
        push = Push(self.package_fn)
        push._start_push()
        request = self.httpd.requests[0]
        request_body = json.loads(request.body.decode())

        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request_body['product_id'], self.product_id)
        self.assertEqual(len(request_body['files']), 2)

    def test_start_push_updates_finish_push_url(self):
        _, finish_url = self.fixture.register_start_push_url(
            self.product_id, self.responses)
        push = Push(self.package_fn)
        push._start_push()
        self.assertEqual(push._finish_push_url, finish_url)

    def test_start_push_updates_files_data(self):
        self.fixture.register_start_push_url(
            self.product_id, self.responses)
        push = Push(self.package_fn)
        push._start_push()
        for file, expected in zip(push.files, self.responses):
            self.assertEqual(file.exists_in_server, expected['exists'])
            self.assertEqual(file.part_upload_urls, expected['urls'])

    def test_finish_push_returns_NONE_when_successful(self):
        url = self.fixture.register_finish_push_url(
            self.product_id, success=True)
        push = Push(self.package_fn)
        push._finish_push_url = url
        observed = push._finish_push()
        self.assertIsNone(observed)

    def test_finish_push_raises_exception_when_fail(self):
        url = self.fixture.register_finish_push_url(
            self.product_id, success=False)
        push = Push(self.package_fn)
        push._finish_push_url = url
        with self.assertRaises(exceptions.FinishPushError):
            push._finish_push()

    def test_finish_push_request_is_made_correctly(self):
        url = self.fixture.register_finish_push_url(
            self.product_id, success=True)
        push = Push(self.package_fn)
        push._finish_push_url = url
        push._finish_push()

        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_upload_files_return_NONE_when_successful(self):
        pkg = self.fixture.set_push(1)
        push = Push(pkg)
        push._start_push()
        observed = push._upload_files()
        self.assertIsNone(observed)

    def test_upload_files_return_NONE_when_file_exists(self):
        pkg = self.fixture.set_push(
            1, success_files=0, existent_files=3)
        push = Push(pkg)
        push._start_push()
        observed = push._upload_files()
        self.assertIsNone(observed)

    def test_upload_files_raises_exception_when_upload_part_fails(self):
        pkg = self.fixture.set_push(
            1, success_files=0, part_fail_files=3)
        push = Push(pkg)
        push._start_push()
        with self.assertRaises(exceptions.FileUploadError):
            push._upload_files()

    def test_upload_files_requests_are_made_correctly(self):
        pkg = self.fixture.set_push(
            1, success_files=2, existent_files=1, file_size=3)
        push = Push(pkg)
        push._start_push()
        push._upload_files()
        # 1 request for starting push
        # 6 requests since 2 files must be uploaded in 3 chunks each
        # Total: 7 requests
        total_requests = 7
        self.assertEqual(len(self.httpd.requests), total_requests)

    def test_push_run_returns_SUCCESS_when_successful(self):
        pkg = self.fixture.set_push(1)
        push = Push(pkg)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.SUCCESS)

    def test_push_run_returns_START_FAIL_when_fail_on_start(self):
        pkg = self.fixture.set_push(1, start_success=False)
        push = Push(pkg)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.START_FAIL)

    def test_push_run_returns_FINISH_FAIL_when_fail_on_finish(self):
        pkg = self.fixture.set_push(1, finish_success=False)
        push = Push(pkg)
        observed = push.run()
        self.assertEqual(observed, PushExitCode.FINISH_FAIL)
