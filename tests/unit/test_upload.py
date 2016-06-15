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
        self.file_name = self.create_empty_file()

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
        part_urls = self.register_file_part_upload_path(4)
        finish_url = self.register_file_finish_upload_path()

        content = b'1234'
        with open(self.file_name, 'wb') as fp:
            fp.write(content)

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = part_urls
        file.finish_upload_url = finish_url
        file.chunk_size = 1
        file.upload()

        self.assertEqual(len(self.handler.requests), 5)
        self.assertEqual(self.handler.requests[0].body, b'1')
        self.assertEqual(self.handler.requests[1].body, b'2')
        self.assertEqual(self.handler.requests[2].body, b'3')
        self.assertEqual(self.handler.requests[3].body, b'4')
        self.assertEqual(self.handler.requests[4].body, b'')

    def test_upload_returns_failure_result_when_part_upload_fails(self):
        part_urls = self.register_file_part_upload_path(success=False)
        finish_url = self.register_file_finish_upload_path()

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = part_urls
        file.finish_upload_url = finish_url
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.PART_FAIL)

    def test_upload_returns_failure_when_finishing_upload_fails(self):
        part_urls = self.register_file_part_upload_path(success=True)
        finish_url = self.register_file_finish_upload_path(success=False)

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = part_urls
        file.finish_upload_url = finish_url
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.FAIL)

    def test_returns_success_when_upload_is_successful(self):
        part_urls = self.register_file_part_upload_path()
        finish_url = self.register_file_finish_upload_path()

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = part_urls
        file.finish_upload_url = finish_url
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.SUCCESS)


class PackageTestCase(BaseTransactionTestCase):

    def test_raises_invalid_package_file_with_inexistent_file(self):
        with self.assertRaises(InvalidPackageFileError):
            Package('inexistent_package_file.json')

    def test_raises_invalid_package_file_when_file_is_not_json(self):
        with self.assertRaises(InvalidPackageFileError):
            Package(__file__)

    def test_can_load_package_file(self):
        project_id = 1
        n_files = 2
        package_fn, files = self.create_stub_package(project_id, n_files)
        package = Package(package_fn)

        self.assertEqual(package.project_id, project_id)
        self.assertEqual(len(package.files), 2)
        for file in package.files:
            self.assertIsInstance(file, File)

    def test_file_id_matches_files_index(self):
        project_id = 1
        n_files = 15
        package_fn, files = self.create_stub_package(project_id, n_files)
        package = Package(package_fn)

        for file in package.files:
            self.assertEqual(package.files.index(file), file.id)


class TransactionTestCase(BaseTransactionTestCase):

    def setUp(self):
        super().setUp()
        self.project_id = 'P1234'
        self.n_files = 2
        package = self.create_stub_package(self.project_id, self.n_files)
        self.package_file, self.files = package

    def test_can_make_initial_payload_correctly(self):
        f1_content = b'spam'
        f1_sha256 = hashlib.sha256(f1_content).hexdigest()
        with open(self.files[0], 'wb') as fp:
            fp.write(f1_content)

        f2_content = b'eggs'
        f2_sha256 = hashlib.sha256(f2_content).hexdigest()
        with open(self.files[1], 'wb') as fp:
            fp.write(f2_content)

        transaction = Transaction(self.package_file)
        observed = json.loads(transaction._initial_payload)

        self.assertEqual(observed['project_id'], self.project_id)
        self.assertEqual(len(observed['files']), self.n_files)
        self.assertEqual(observed['files'][0]['sha256'], f1_sha256)
        self.assertEqual(observed['files'][1]['sha256'], f2_sha256)

    def test_can_retrieve_host_url_by_hardcode(self):
        del os.environ['EFU_SERVER_URL']
        transaction = Transaction(self.package_file)
        expected = 'http://0.0.0.0/project/P1234/upload/'
        observed = transaction._start_transaction_url
        self.assertEqual(observed, expected)

    def test_can_retrieve_host_url_by_environment_variable(self):
        os.environ['EFU_SERVER_URL'] = 'http://spam.eggs.com'
        transaction = Transaction(self.package_file)
        expected = 'http://spam.eggs.com/project/P1234/upload/'
        observed = transaction._start_transaction_url
        self.assertEqual(observed, expected)

    def test_start_transaction_returns_TRUE_when_successful(self):
        self.register_start_transaction_path(self.project_id, self.n_files)
        transaction = Transaction(self.package_file)
        observed = transaction._start_transaction()
        self.assertTrue(observed)

    def test_start_transaction_returns_FALSE_when_fail(self):
        self.register_start_transaction_path(
            self.project_id,
            self.n_files,
            start_success=False
        )
        transaction = Transaction(self.package_file)
        observed = transaction._start_transaction()
        self.assertFalse(observed)

    def test_start_transaction_request_is_made_correctly(self):
        start_url, finish_url = self.register_start_transaction_path(
            self.project_id,
            self.n_files
        )
        transaction = Transaction(self.package_file)
        transaction._start_transaction()
        request = self.handler.requests[0]
        request_body = json.loads(request.body.decode())

        self.assertEqual(len(self.handler.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request_body['project_id'], self.project_id)
        self.assertEqual(len(request_body['files']), 2)

    def test_start_transaction_updates_finish_transaction_url(self):
        start_url, finish_url = self.register_start_transaction_path(
            self.project_id,
            self.n_files
        )
        transaction = Transaction(self.package_file)
        transaction._start_transaction()
        self.assertEqual(transaction._finish_transaction_url, finish_url)

    def test_start_transaction_updates_files_data(self):
        chunk_size = 1
        part_urls = self.register_file_part_upload_path()
        finish_url = self.register_file_finish_upload_path()
        files = [
            self.create_existing_file_response(0),
            self.create_non_existing_file_response(
                1, chunk_size, part_urls, finish_url)
        ]
        self.register_start_transaction_path(
            self.project_id, self.n_files, files=files)

        transaction = Transaction(self.package_file)
        transaction._start_transaction()

        file = transaction.files[0]
        self.assertTrue(file.exists_in_server)
        self.assertEqual(file.chunk_size, None)
        self.assertEqual(file.part_upload_urls, None)
        self.assertEqual(file.finish_upload_url, None)

        file = transaction.files[1]
        self.assertFalse(file.exists_in_server)
        self.assertEqual(file.chunk_size, chunk_size)
        self.assertEqual(file.part_upload_urls, part_urls)
        self.assertEqual(file.finish_upload_url, finish_url)

    def test_finish_transaction_returns_TRUE_when_successful(self):
        url = self.register_finish_transaction_path(success=True)
        transaction = Transaction(self.package_file)
        transaction._finish_transaction_url = url

        observed = transaction._finish_transaction()
        self.assertTrue(observed)

    def test_finish_transaction_returns_FALSE_when_fail(self):
        url = self.register_finish_transaction_path(success=False)
        transaction = Transaction(self.package_file)
        transaction._finish_transaction_url = url

        observed = transaction._finish_transaction()
        self.assertFalse(observed)

    def test_finish_transaction_request_is_made_correctly(self):
        url = self.register_finish_transaction_path(success=True)
        transaction = Transaction(self.package_file)
        transaction._finish_transaction_url = url
        transaction._finish_transaction()

        request = self.handler.requests[0]

        self.assertEqual(len(self.handler.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_can_upload_files(self):
        n_files = 3
        pkg = self.set_complete_transaction_response(n_success_files=n_files)
        transaction = Transaction(pkg)
        transaction._start_transaction()
        uploads = transaction._upload_files()
        self.assertEqual(len(uploads), n_files)
        for file, result in uploads:
            self.assertEqual(result, UploadStatus.SUCCESS)

    def test_transaction_run_returns_TRUE_when_successful(self):
        pkg = self.set_complete_transaction_response()
        transaction = Transaction(pkg)
        success, uploads = transaction.run()
        self.assertTrue(success)
        for file, result in uploads:
            self.assertEqual(result, UploadStatus.SUCCESS)

    def test_transaction_run_returns_FALSE_when_fail_on_start(self):
        pkg = self.set_complete_transaction_response(start_success=False)
        transaction = Transaction(pkg)
        success, uploads = transaction.run()
        self.assertFalse(success)

    def test_transaction_run_returns_FALSE_when_fail_on_finish(self):
        pkg = self.set_complete_transaction_response(finish_success=False)
        transaction = Transaction(pkg)
        success, uploads = transaction.run()
        self.assertFalse(success)
