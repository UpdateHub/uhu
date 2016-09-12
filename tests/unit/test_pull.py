# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os

from efu.core import Object, Package
from efu.core.exceptions import PackageObjectExistsError
from efu.transactions.pull import Pull, DownloadObjectStatus
from efu.transactions.exceptions import CommitDoesNotExist

from ..base import EFUTestCase, PullMockMixin


class PullTestCase(PullMockMixin, EFUTestCase):

    def setUp(self):
        super().setUp()
        self.set_directories()
        self.set_file_image()
        self.set_commit()
        self.set_package_var()
        self.full_package = {
            'product': self.product_id,
            'objects': {
                self.image_fn: {
                    'install-mode': 'raw',
                    'target-device': 'device'
                }
            }
        }
        with open(self.package_fn, 'w') as fp:
            json.dump(self.full_package, fp)

        with open(self.image_fn, 'bw') as fp:
            fp.write(self.image_content)

        # fixtures
        self.metadata = Package(self.version).metadata.serialize()
        self.image_metadata = self.metadata['images'][0]

        # create clean package file
        with open(self.package_fn, 'w') as fp:
            json.dump({'product': self.product_id}, fp)

        self.set_urls()

    def test_can_download_metadata(self):
        pull = Pull(self.commit)
        observed = pull.get_metadata()
        self.assertEqual(observed, self.metadata)

    def test_get_metadata_creates_a_commit_file(self):
        pull = Pull(self.commit)
        self.assertFalse(os.path.exists(self.commit_file))
        pull.get_metadata()
        self.assertTrue(os.path.exists(self.commit_file))
        with open(self.commit_file) as fp:
            observed = json.load(fp)
        self.assertEqual(observed, self.metadata)

    def test_get_metadata_raises_error_when_metadata_does_not_exist(self):
        self.httpd.register_response(
            '/products/{}/commits/1'.format(self.product_id, self.commit),
            'GET', status_code=404)
        pull = Pull(1)
        with self.assertRaises(CommitDoesNotExist):
            pull.get_metadata()

    def test_check_local_files_returns_NONE_when_identical_file_exists(self):
        pull = Pull(self.commit)
        observed = pull.check_local_files(self.metadata['images'])
        self.assertIsNone(observed)

    def test_check_local_files_returns_NONE_when_file_does_not_exists(self):
        os.remove(self.image_fn)
        pull = Pull(self.commit)
        observed = pull.check_local_files(self.metadata['images'])
        self.assertIsNone(observed)

    def test_check_local_files_raises_error_when_existent_file_diverges(self):
        with open(self.image_fn, 'w') as fp:
            fp.write('overwrited')
        pull = Pull(self.commit)
        with self.assertRaises(FileExistsError):
            pull.check_local_files(self.metadata['images'])

    def test_get_object_returns_EXISTS_when_file_exists(self):
        pull = Pull(self.commit)
        pull.existent_files.append(self.image_fn)
        expected = DownloadObjectStatus.EXISTS
        observed = pull._get_object(self.image_metadata)
        self.assertEqual(observed, expected)
        # If file exists, no requests must be made
        self.assertEqual(len(self.httpd.requests), 0)

    def test_get_object_returns_SUCCESS_when_file_does_not_exist(self):
        os.remove(self.image_fn)
        pull = Pull(self.commit)
        expected = DownloadObjectStatus.SUCCESS
        observed = pull._get_object(self.image_metadata)
        self.assertEqual(observed, expected)
        # If file does not exist, 1 request must be made
        self.assertEqual(len(self.httpd.requests), 1)

    def test_get_object_returns_ERROR_when_server_fails(self):
        os.remove(self.image_fn)
        path = '/products/{}/objects/{}'.format(
            self.product_id, self.image_sha256sum)
        self.httpd.register_response(
            path, 'GET', body=self.image_content, status_code=500)
        pull = Pull(self.commit)
        expected = DownloadObjectStatus.ERROR
        observed = pull._get_object(self.image_metadata)
        self.assertEqual(observed, expected)

    def test_file_integrity_after_download(self):
        os.remove(self.image_fn)
        pull = Pull(self.commit)
        pull._get_object(self.image_metadata)
        with open(self.image_fn, 'rb') as fp:
            observed = hashlib.sha256(fp.read()).hexdigest()
        self.assertEqual(observed, self.image_sha256sum)

    def test_pull_with_no_existent_objects(self):
        os.remove(self.image_fn)
        expected = [DownloadObjectStatus.SUCCESS]
        observed = Pull(self.commit).pull(full=True)
        self.assertEqual(expected, observed)

    def test_pull_with_existent_objects(self):
        expected = [DownloadObjectStatus.EXISTS]
        observed = Pull(self.commit).pull(full=True)
        self.assertEqual(expected, observed)

    def test_pull_with_download_error(self):
        os.remove(self.image_fn)
        path = '/products/{}/objects/{}'.format(
            self.product_id, self.image_sha256sum)
        self.httpd.register_response(
            path, 'GET', body=self.image_content, status_code=500)
        expected = [DownloadObjectStatus.ERROR]
        observed = Pull(self.commit).pull(full=True)
        self.assertEqual(expected, observed)

    def test_can_abort_pull_when_files_diverges(self):
        with open(self.image_fn, 'w') as fp:
            fp.write('overwrited')
        with self.assertRaises(FileExistsError):
            Pull(self.commit).pull(full=True)

    def test_pull_raises_error_if_package_file_exists(self):
        with open(self.package_fn, 'w') as fp:
            json.dump(self.full_package, fp)
        pull = Pull(self.commit)
        with self.assertRaises(PackageObjectExistsError):
            pull.pull(full=True)
        with self.assertRaises(PackageObjectExistsError):
            pull.pull(full=False)

    def test_pull_does_not_download_files_if_full_is_false(self):
        os.remove(self.image_fn)
        self.assertFalse(os.path.exists(self.image_fn))
        Pull(self.commit).pull(full=False)
        self.assertFalse(os.path.exists(self.image_fn))

    def test_pull_downloads_files_if_full_is_true(self):
        os.remove(self.image_fn)
        self.assertFalse(os.path.exists(self.image_fn))
        Pull(self.commit).pull(full=True)
        self.assertTrue(os.path.exists(self.image_fn))
