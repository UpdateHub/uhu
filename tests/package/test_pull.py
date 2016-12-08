# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from efu.core.package import Package

from utils import BasePullTestCase


class PackagePullTestCase(BasePullTestCase):

    def test_can_download_metadata(self):
        metadata = self.package.download_metadata(self.pkg_uid)
        self.assertEqual(metadata, self.metadata)

    def test_get_metadata_raises_error_when_metadata_does_not_exist(self):
        self.httpd.register_response(
            '/products/{}/packages/{}'.format(self.product, self.pkg_uid),
            'GET', status_code=404)
        with self.assertRaises(ValueError):
            self.package.download_metadata(self.pkg_uid)

    def test_get_download_list_returns_empty_list_with_identical_file(self):
        with open(self.obj_fn, 'bw') as fp:
            fp.write(self.obj_content)
        package = Package.from_metadata(self.metadata)
        objects = package.get_download_list()
        self.assertTrue(os.path.exists(self.obj_fn))
        self.assertEqual(len(objects), 0)

    def test_get_download_list_returns_objects_when_file_does_not_exists(self):
        package = Package.from_metadata(self.metadata)
        objects = package.get_download_list()
        self.assertFalse(os.path.exists(self.obj_fn))
        self.assertEqual(len(objects), 1)

    def test_get_download_list_raises_error_when_existent_file_diverges(self):
        content = 'overwrited'
        with open(self.obj_fn, 'w') as fp:
            fp.write(content)
        package = Package.from_metadata(self.metadata)
        with self.assertRaises(FileExistsError):
            package.get_download_list()
        with open(self.obj_fn) as fp:
            self.assertEqual(fp.read(), content)

    def test_pull_raises_error_when_objects_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('overwritten')
        with self.assertRaises(FileExistsError):
            self.package.pull(self.pkg_uid, objects=True)

    def test_pull_downloads_files_if_full_is_True(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        self.package.pull(self.pkg_uid, objects=True)
        self.assertTrue(os.path.exists(self.obj_fn))

    def test_pull_does_not_download_files_if_full_is_False(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        self.package.pull(self.pkg_uid, objects=False)
        self.assertFalse(os.path.exists(self.obj_fn))
