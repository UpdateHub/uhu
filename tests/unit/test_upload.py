# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os
import unittest
from itertools import count
from unittest.mock import patch

from efu.upload.upload import File, Package, Transaction, UploadStatus
from efu.upload.exceptions import InvalidPackageFileError, InvalidFileError

from ..base import BaseTransactionTestCase


class FileTestCase(BaseTransactionTestCase):

    def setUp(self):
        super().setUp()
        self.file_name = self.fixture.create_file(b'\0')

    def test_can_reset_file_id_generation(self):
        f1 = File(self.file_name)
        f2 = File(self.file_name)
        f3 = File(self.file_name)
        self.assertEqual((f1.id, f2.id, f3.id), (0, 1, 2))

        File._File__reset_id_generator()

        f4 = File(self.file_name)
        f5 = File(self.file_name)
        f6 = File(self.file_name)
        self.assertEqual((f4.id, f5.id, f6.id), (0, 1, 2))

    def test_file_validation(self):
        with self.assertRaises(InvalidFileError):
            File('inexistent_file.bin')

    def test_file_sha256(self):
        content = b'0'
        sha256 = hashlib.sha256(content).hexdigest()
        with open(self.file_name, 'wb') as fp:
            fp.write(content)

        file = File(self.file_name)
        self.assertEqual(file.sha256, sha256)

    def test_file_id(self):
        file = File(self.file_name)
        self.assertEqual(file.id, 0)

        file = File(self.file_name)
        self.assertEqual(file.id, 1)

        file = File(self.file_name)
        self.assertEqual(file.id, 2)

    def test_does_not_upload_when_file_exists_in_server(self):
        file = File(self.file_name)
        file.exists_in_server = True
        result = file.upload()
        self.assertEqual(result, UploadStatus.EXISTS)

    def test_upload_requests_payload_are_made_correctly(self):
        fn, conf = self.fixture.set_file(1, 1, content=b'1234', chunk_size=1)

        file = File(fn)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1
        file.upload()

        self.assertEqual(len(self.httpd.requests), 5)
        self.assertEqual(self.httpd.requests[0].body, b'1')
        self.assertEqual(self.httpd.requests[1].body, b'2')
        self.assertEqual(self.httpd.requests[2].body, b'3')
        self.assertEqual(self.httpd.requests[3].body, b'4')
        self.assertEqual(self.httpd.requests[4].body, b'')

    def test_upload_returns_failure_result_when_part_upload_fails(self):
        fn, conf = self.fixture.set_file(1, 1, part_success=False)

        file = File(fn)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.PART_FAIL)

    def test_upload_returns_failure_when_finishing_upload_fails(self):
        fn, conf = self.fixture.set_file(1, 1, finish_success=False)

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.FAIL)

    def test_returns_success_when_upload_is_successful(self):
        fn, conf = self.fixture.set_file(1, 1)

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.SUCCESS)


class PackageTestCase(BaseTransactionTestCase):

    def setUp(self):
        super().setUp()
        self.project_id = 1

    def test_raises_invalid_package_file_with_inexistent_file(self):
        with self.assertRaises(InvalidPackageFileError):
            Package('inexistent_package_file.json')

    def test_raises_invalid_package_file_when_file_is_not_json(self):
        with self.assertRaises(InvalidPackageFileError):
            Package(__file__)

    def test_can_load_package_file(self):
        files = [self.fixture.create_file(b'0') for _ in range(2)]
        package_fn = self.fixture.set_package(self.project_id, files)

        package = Package(package_fn)

        self.assertEqual(package.project_id, self.project_id)
        self.assertEqual(len(package.files), len(files))
        for file in package.files:
            self.assertIsInstance(file, File)

    def test_file_id_matches_files_index(self):
        files = [self.fixture.create_file(b'0') for _ in range(15)]
        package_fn = self.fixture.set_package(self.project_id, files)
        package = Package(package_fn)

        for file in package.files:
            self.assertEqual(package.files.index(file), file.id)


class TransactionTestCase(BaseTransactionTestCase):

    def setUp(self):
        super().setUp()
        self.project_id = 'P1234'
        base_files = [
            self.fixture.set_file(self.project_id, 0, exists=True),
            self.fixture.set_file(self.project_id, 1, exists=False),
        ]
        self.files, self.responses = [], []
        for file, response in base_files:
            self.files.append(file)
            self.responses.append(response)
        self.package_fn = self.fixture.set_package(self.project_id, self.files)

    def test_can_make_initial_payload_correctly(self):
        project_id = 123
        files, hashes = [], []
        for content in (b'spam', b'eggs'):
            files.append(self.fixture.create_file(content))
            hashes.append(hashlib.sha256(content).hexdigest())

        pkg = self.fixture.set_package(project_id, files)
        transaction = Transaction(pkg)
        payload = json.loads(transaction._initial_payload)

        self.assertEqual(payload['project_id'], project_id)
        self.assertEqual(len(payload['files']), len(files))
        for observed, expected in zip(payload['files'], hashes):
            self.assertEqual(observed['sha256'], expected)

    def test_can_retrieve_host_url_by_hardcode(self):
        del os.environ['EFU_SERVER_URL']
        transaction = Transaction(self.package_fn)
        expected = 'http://0.0.0.0/project/P1234/upload/'
        observed = transaction._start_transaction_url
        self.assertEqual(observed, expected)

    def test_can_retrieve_host_url_by_environment_variable(self):
        os.environ['EFU_SERVER_URL'] = 'http://spam.eggs.com'
        transaction = Transaction(self.package_fn)
        expected = 'http://spam.eggs.com/project/P1234/upload/'
        observed = transaction._start_transaction_url
        self.assertEqual(observed, expected)

    def test_start_transaction_returns_TRUE_when_successful(self):
        self.fixture.register_start_transaction_url(
            self.project_id, self.responses)
        transaction = Transaction(self.package_fn)
        observed = transaction._start_transaction()
        self.assertTrue(observed)

    def test_start_transaction_returns_FALSE_when_fail(self):
        self.fixture.register_start_transaction_url(
            self.project_id, self.files, start_success=False)
        transaction = Transaction(self.package_fn)
        observed = transaction._start_transaction()
        self.assertFalse(observed)

    def test_start_transaction_request_is_made_correctly(self):
        start_url, finish_url = self.fixture.register_start_transaction_url(
            self.project_id, self.responses)
        transaction = Transaction(self.package_fn)
        transaction._start_transaction()
        request = self.httpd.requests[0]
        request_body = json.loads(request.body.decode())

        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request_body['project_id'], self.project_id)
        self.assertEqual(len(request_body['files']), 2)

    def test_start_transaction_updates_finish_transaction_url(self):
        start_url, finish_url = self.fixture.register_start_transaction_url(
            self.project_id, self.responses)
        transaction = Transaction(self.package_fn)
        transaction._start_transaction()
        self.assertEqual(transaction._finish_transaction_url, finish_url)

    def test_start_transaction_updates_files_data(self):
        self.fixture.register_start_transaction_url(
            self.project_id, self.responses)
        transaction = Transaction(self.package_fn)
        transaction._start_transaction()
        for file, expected in zip(transaction.files, self.responses):
            self.assertEqual(file.exists_in_server, expected['exists'])
            self.assertEqual(file.chunk_size, expected['chunk_size'])
            self.assertEqual(file.part_upload_urls, expected['urls'])
            self.assertEqual(file.finish_upload_url,
                             expected['finish_upload_url'])

    def test_finish_transaction_returns_TRUE_when_successful(self):
        url = self.fixture.register_finish_transaction_url(
            self.project_id, success=True)
        transaction = Transaction(self.package_fn)
        transaction._finish_transaction_url = url

        observed = transaction._finish_transaction()
        self.assertTrue(observed)

    def test_finish_transaction_returns_FALSE_when_fail(self):
        url = self.fixture.register_finish_transaction_url(
            self.project_id, success=False)
        transaction = Transaction(self.package_fn)
        transaction._finish_transaction_url = url

        observed = transaction._finish_transaction()
        self.assertFalse(observed)

    def test_finish_transaction_request_is_made_correctly(self):
        url = self.fixture.register_finish_transaction_url(
            self.project_id, success=True)
        transaction = Transaction(self.package_fn)
        transaction._finish_transaction_url = url
        transaction._finish_transaction()

        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_can_upload_files(self):
        n_files = 3
        pkg = self.fixture.set_transaction(1, success_files=n_files)
        transaction = Transaction(pkg)
        transaction._start_transaction()
        uploads = transaction._upload_files()
        self.assertEqual(len(uploads), n_files)
        for file, result in uploads:
            self.assertEqual(result, UploadStatus.SUCCESS)

    def test_transaction_run_returns_TRUE_when_successful(self):
        pkg = self.fixture.set_transaction(1)
        transaction = Transaction(pkg)
        success, uploads = transaction.run()
        self.assertTrue(success)
        for file, result in uploads:
            self.assertEqual(result, UploadStatus.SUCCESS)

    def test_transaction_run_returns_FALSE_when_fail_on_start(self):
        pkg = self.fixture.set_transaction(1, start_success=False)
        transaction = Transaction(pkg)
        success, uploads = transaction.run()
        self.assertFalse(success)

    def test_transaction_run_returns_FALSE_when_fail_on_finish(self):
        pkg = self.fixture.set_transaction(1, finish_success=False)
        transaction = Transaction(pkg)
        success, uploads = transaction.run()
        self.assertFalse(success)
