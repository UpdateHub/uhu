# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os

from efu.core import Object, Package
from efu.transactions.pull import Pull, DownloadObjectStatus

from ..base import PullMockMixin, BaseTestCase


class PullTestCase(PullMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.set_directories()
        self.set_object()
        self.set_package_id()
        self.set_package_var()
        self.full_package = {
            'product': self.product,
            'objects': {
                self.obj_fn: {
                    'mode': 'raw',
                    'target-device': 'device'
                }
            }
        }
        with open(self.pkg_file, 'w') as fp:
            json.dump(self.full_package, fp)

        with open(self.obj_fn, 'bw') as fp:
            fp.write(self.obj_content)

        # fixtures
        self.metadata = Package.from_file(self.pkg_file).metadata.serialize()
        self.obj_metadata = self.metadata['objects'][0]

        # create clean package file
        with open(self.pkg_file, 'w') as fp:
            json.dump({'product': self.product}, fp)

        self.set_urls()

    def test_can_download_metadata(self):
        pull = Pull(self.product, self.package_id)
        observed = pull.get_metadata()
        self.assertEqual(observed, self.metadata)

    def test_get_metadata_raises_error_when_metadata_does_not_exist(self):
        self.httpd.register_response(
            '/products/{}/packages/1'.format(self.product, self.package_id),
            'GET', status_code=404)
        pull = Pull(self.product, 1)
        with self.assertRaises(ValueError):
            pull.get_metadata()

    def test_check_local_files_returns_NONE_when_identical_file_exists(self):
        pull = Pull(self.product, self.package_id)
        observed = pull.check_local_files(self.metadata['objects'])
        self.assertIsNone(observed)

    def test_check_local_files_returns_NONE_when_file_does_not_exists(self):
        os.remove(self.obj_fn)
        pull = Pull(self.product, self.package_id)
        observed = pull.check_local_files(self.metadata['objects'])
        self.assertIsNone(observed)

    def test_check_local_files_raises_error_when_existent_file_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('overwrited')
        pull = Pull(self.product, self.package_id)
        with self.assertRaises(FileExistsError):
            pull.check_local_files(self.metadata['objects'])

    def test_get_object_returns_EXISTS_when_file_exists(self):
        pull = Pull(self.product, self.package_id)
        pull.existent_files.append(self.obj_fn)
        expected = DownloadObjectStatus.EXISTS
        observed = pull._get_object(self.obj_metadata)
        self.assertEqual(observed, expected)
        # If file exists, no requests must be made
        self.assertEqual(len(self.httpd.requests), 0)

    def test_get_object_returns_SUCCESS_when_file_does_not_exist(self):
        os.remove(self.obj_fn)
        pull = Pull(self.product, self.package_id)
        expected = DownloadObjectStatus.SUCCESS
        observed = pull._get_object(self.obj_metadata)
        self.assertEqual(observed, expected)
        # If file does not exist, 1 request must be made
        self.assertEqual(len(self.httpd.requests), 1)

    def test_get_object_returns_ERROR_when_server_fails(self):
        os.remove(self.obj_fn)
        path = '/products/{}/objects/{}'.format(
            self.product, self.obj_sha256sum)
        self.httpd.register_response(
            path, 'GET', body=self.obj_content, status_code=500)
        pull = Pull(self.product, self.package_id)
        expected = DownloadObjectStatus.ERROR
        observed = pull._get_object(self.obj_metadata)
        self.assertEqual(observed, expected)

    def test_file_integrity_after_download(self):
        os.remove(self.obj_fn)
        pull = Pull(self.product, self.package_id)
        pull._get_object(self.obj_metadata)
        with open(self.obj_fn, 'rb') as fp:
            observed = hashlib.sha256(fp.read()).hexdigest()
        self.assertEqual(observed, self.obj_sha256sum)

    def test_can_abort_pull_when_files_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('overwrited')
        with self.assertRaises(FileExistsError):
            Pull(self.product, self.package_id).pull(full=True)

    def test_pull_does_not_download_files_if_full_is_false(self):
        os.remove(self.obj_fn)
        self.assertFalse(os.path.exists(self.obj_fn))
        Pull(self.product, self.package_id).pull(full=False)
        self.assertFalse(os.path.exists(self.obj_fn))

    def test_pull_downloads_files_if_full_is_true(self):
        os.remove(self.obj_fn)
        self.assertFalse(os.path.exists(self.obj_fn))
        Pull(self.product, self.package_id).pull(full=True)
        self.assertTrue(os.path.exists(self.obj_fn))
