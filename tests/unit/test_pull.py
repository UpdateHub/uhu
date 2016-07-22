# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os

from efu.push.file import File
from efu.push.package import Package
from efu.pull.pull import Pull, DownloadObjectStatus

from ..base import EFUTestCase


class PullTestCase(EFUTestCase):

    def remove_file(self):
        try:
            os.remove(self.file)
        except:
            # file already deleted
            pass

    def setUp(self):
        super().setUp()
        self.product = '1234'
        self.version = '2.0'
        self.file = 'image.bin'
        self.commit = '4321'
        self.file_content = b'123456789'

        with open(self.file, 'bw') as fp:
            fp.write(self.file_content)
        self.addCleanup(self.remove_file)

        pkg = self.create_package_file(
            self.product, self.version, [self.file])

        self.metadata = Package(pkg).metadata
        self.file_metadata = self.metadata['images'][0]
        self.file_sha256sum = self.file_metadata['sha256sum']
        self.httpd.register_response(
            '/products/{}/commits/{}'.format(self.product, self.commit),
            'GET', body=json.dumps(self.metadata), status_code=200)

        path = '/products/{}/objects/{}'.format(
            self.product, self.file_sha256sum)
        self.httpd.register_response(
            path, 'GET', body=self.file_content, status_code=200)

    def test_get_metadata(self):
        pull = Pull(self.product, self.commit)
        observed = pull.get_metadata()
        self.assertEqual(observed, self.metadata)

    def test_get_metadata_returns_NONE_when_metadata_does_not_exist(self):
        self.httpd.register_response(
            '/products/{}/commits/1'.format(self.product, self.commit),
            'GET', status_code=404)
        pull = Pull(self.product, 1)
        observed = pull.get_metadata()
        self.assertIsNone(observed)

    def test_can_download_returns_TRUE_when_identical_file_exists(self):
        pull = Pull(self.product, self.commit)
        observed = pull.can_download(self.metadata['images'])
        self.assertTrue(observed)

    def test_can_download_returns_TRUE_when_file_does_not_exists(self):
        os.remove(self.file)
        pull = Pull(self.product, self.commit)
        observed = pull.can_download(self.metadata['images'])
        self.assertTrue(observed)

    def test_can_download_returns_FALSE_when_existent_file_diverges(self):
        with open(self.file, 'w') as fp:
            fp.write('overwrited')
        pull = Pull(self.product, self.commit)
        observed = pull.can_download(self.metadata['images'])
        self.assertFalse(observed)

    def test_get_object_returns_EXISTS_when_file_exists(self):
        pull = Pull(self.product, self.commit)
        pull.existent_files.append(self.file)
        expected = DownloadObjectStatus.EXISTS
        observed = pull._get_object(self.file_metadata)
        self.assertEqual(observed, expected)
        # If file exists, no requests must be made
        self.assertEqual(len(self.httpd.requests), 0)

    def test_get_object_returns_SUCCESS_when_file_does_not_exist(self):
        os.remove(self.file)
        pull = Pull(self.product, self.commit)
        expected = DownloadObjectStatus.SUCCESS
        observed = pull._get_object(self.file_metadata)
        self.assertEqual(observed, expected)
        # If file does not exist, 1 request must be made
        self.assertEqual(len(self.httpd.requests), 1)

    def test_get_object_returns_ERROR_when_server_fails(self):
        os.remove(self.file)
        path = '/products/{}/objects/{}'.format(
            self.product, self.file_sha256sum)
        self.httpd.register_response(
            path, 'GET', body=self.file_content, status_code=500)
        pull = Pull(self.product, self.commit)
        expected = DownloadObjectStatus.ERROR
        observed = pull._get_object(self.file_metadata)
        self.assertEqual(observed, expected)

    def test_file_integrity_after_download(self):
        os.remove(self.file)
        pull = Pull(self.product, self.commit)
        pull._get_object(self.file_metadata)
        with open(self.file, 'rb') as fp:
            observed = hashlib.sha256(fp.read()).hexdigest()
        self.assertEqual(observed, self.file_sha256sum)

    def test_pull_with_no_existent_objects(self):
        os.remove(self.file)
        expected = [DownloadObjectStatus.SUCCESS]
        observed = Pull(self.product, self.commit).pull()
        self.assertEqual(expected, observed)

    def test_pull_with_existent_objects(self):
        expected = [DownloadObjectStatus.EXISTS]
        observed = Pull(self.product, self.commit).pull()
        self.assertEqual(expected, observed)

    def test_pull_with_download_error(self):
        os.remove(self.file)
        path = '/products/{}/objects/{}'.format(
            self.product, self.file_sha256sum)
        self.httpd.register_response(
            path, 'GET', body=self.file_content, status_code=500)
        expected = [DownloadObjectStatus.ERROR]
        observed = Pull(self.product, self.commit).pull()
        self.assertEqual(expected, observed)

    def test_can_abort_pull_when_files_diverges(self):
        with open(self.file, 'w') as fp:
            fp.write('overwrited')
        observed = Pull(self.product, self.commit).pull()
        self.assertIsNone(observed)
