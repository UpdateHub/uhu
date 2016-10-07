# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os
import tempfile
import shutil

from efu.core import Object, Package
from efu.transactions.pull import Pull, DownloadObjectResult
from efu.utils import LOCAL_CONFIG_VAR, SERVER_URL_VAR

from ..utils import (
    EFUTestCase, HTTPTestCaseMixin, FileFixtureMixin, EnvironmentFixtureMixin)


class BasePullTestCase(EnvironmentFixtureMixin, FileFixtureMixin,
                       HTTPTestCaseMixin, EFUTestCase):

    def setUp(self):
        wd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, wd)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(wd)

        self.pkg_fn = os.path.join(wd, '.efu')
        self.set_env_var(LOCAL_CONFIG_VAR, self.pkg_fn)

        self.product = '1324'
        self.pkg_uid = '1234'
        self.package = Package(uid=self.pkg_uid, product=self.product)

        # object
        self.obj_id = 1
        self.obj_fn = 'image.bin'
        self.obj_content = b'spam'
        self.obj_sha256 = hashlib.sha256(self.obj_content).hexdigest()
        self.addCleanup(self.remove_file, self.obj_fn)

        self.metadata = {
            'product': self.product,
            'version': '2.0',
            'objects': [
                {
                    'filename': self.obj_fn,
                    'mode': 'raw',
                    'target-device': '/device',
                    'size': 4,
                    'sha256sum': hashlib.sha256(self.obj_content).hexdigest()
                }
            ]
        }

        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        # url to download metadata
        self.httpd.register_response(
            '/products/{}/packages/{}'.format(self.product, self.pkg_uid),
            'GET', body=json.dumps(self.metadata), status_code=200)

        # url to download object
        self.httpd.register_response(
            '/products/{}/objects/{}'.format(self.product, self.obj_sha256),
            'GET', body=self.obj_content, status_code=200)


class PullTestCase(BasePullTestCase):

    def test_can_download_metadata(self):
        pull = Pull(self.package)
        pull.get_metadata()
        self.assertEqual(pull.metadata, self.metadata)

    def test_get_metadata_raises_error_when_metadata_does_not_exist(self):
        self.httpd.register_response(
            '/products/{}/packages/{}'.format(self.product, self.pkg_uid),
            'GET', status_code=404)
        pull = Pull(self.package)
        with self.assertRaises(ValueError):
            pull.get_metadata()

    def test_check_local_files_returns_None_when_identical_file_exists(self):
        with open(self.obj_fn, 'bw') as fp:
            fp.write(self.obj_content)
        pull = Pull(self.package)
        observed = pull.check_local_files(Package.from_metadata(self.metadata))
        self.assertTrue(os.path.exists(self.obj_fn))
        self.assertIsNone(observed)

    def test_check_local_files_returns_None_when_file_does_not_exists(self):
        pull = Pull(self.package)
        observed = pull.check_local_files(Package.from_metadata(self.metadata))
        self.assertFalse(os.path.exists(self.obj_fn))
        self.assertIsNone(observed)

    def test_check_local_files_raises_error_when_existent_file_diverges(self):
        content = 'overwrited'
        with open(self.obj_fn, 'w') as fp:
            fp.write(content)
        pull = Pull(self.package)
        with self.assertRaises(FileExistsError):
            pull.check_local_files(Package.from_metadata(self.metadata))
        with open(self.obj_fn) as fp:
            self.assertEqual(fp.read(), content)

    def test_download_object_returns_EXISTS_when_file_exists(self):
        with open(self.obj_fn, 'bw') as fp:
            fp.write(self.obj_content)
        pull = Pull(self.package)
        pkg = Package.from_metadata(self.metadata)
        pull.existent_files.append(self.obj_fn)
        expected = DownloadObjectResult.EXISTS
        observed = pull.download_object(pkg.objects.get(self.obj_id))
        self.assertEqual(observed, expected)
        # If file exists, no requests must be made
        self.assertEqual(len(self.httpd.requests), 0)

    def test_download_object_returns_SUCCESS_when_file_does_not_exist(self):
        pull = Pull(self.package)
        pkg = Package.from_metadata(self.metadata)
        expected = DownloadObjectResult.SUCCESS
        observed = pull.download_object(pkg.objects.get(self.obj_id))
        self.assertEqual(observed, expected)
        # If file does not exist, 1 request must be made
        self.assertEqual(len(self.httpd.requests), 1)

    def test_download_object_returns_ERROR_when_server_fails(self):
        path = '/products/{}/objects/{}'.format(
            self.product, self.obj_sha256)
        self.httpd.register_response(path, 'GET', status_code=500)
        pull = Pull(self.package)
        pkg = Package.from_metadata(self.metadata)
        expected = DownloadObjectResult.ERROR
        observed = pull.download_object(pkg.objects.get(self.obj_id))
        self.assertEqual(observed, expected)

    def test_file_integrity_after_download(self):
        pull = Pull(self.package)
        pkg = Package.from_metadata(self.metadata)
        pull.download_object(pkg.objects.get(self.obj_id))
        with open(self.obj_fn, 'rb') as fp:
            observed = hashlib.sha256(fp.read()).hexdigest()
        self.assertEqual(observed, self.obj_sha256)

    def test_can_abort_pull_when_files_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('overwrited')
        with self.assertRaises(FileExistsError):
            self.package.pull(full=True)

    def test_pull_downloads_files_if_full_is_True(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        self.package.pull(full=True)
        self.assertTrue(os.path.exists(self.obj_fn))

    def test_pull_does_not_download_files_if_full_is_False(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        self.package.pull(full=False)
        self.assertFalse(os.path.exists(self.obj_fn))
