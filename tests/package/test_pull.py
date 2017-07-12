# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os

from uhu.core.package import Package
from uhu.exceptions import DownloadError
from uhu.utils import SERVER_URL_VAR

from utils import BasePullTestCase


class PackagePullTestCase(BasePullTestCase):

    def test_can_download_metadata(self):
        metadata = self.package.download_metadata(self.pkg_uid)
        self.assertEqual(metadata, self.metadata)

    def test_download_metadata_raises_error_when_package_does_not_exist(self):
        self.httpd.register_response(
            '/packages/{}'.format(self.pkg_uid), 'GET', status_code=404)
        with self.assertRaises(DownloadError):
            self.package.download_metadata(self.pkg_uid)

    def test_get_download_list_returns_empty_list_with_identical_file(self):
        with open(self.obj_fn, 'bw') as fp:
            fp.write(self.obj_content)
        package = Package(dump=self.metadata)
        objects = package.get_download_list()
        self.assertTrue(os.path.exists(self.obj_fn))
        self.assertEqual(len(objects), 0)

    def test_get_download_list_returns_objects_when_file_does_not_exists(self):
        package = Package(dump=self.metadata)
        objects = package.get_download_list()
        self.assertFalse(os.path.exists(self.obj_fn))
        self.assertEqual(len(objects), 1)

    def test_get_download_list_raises_error_when_existent_file_diverges(self):
        content = 'overwrited'
        with open(self.obj_fn, 'w') as fp:
            fp.write(content)
        package = Package(dump=self.metadata)
        with self.assertRaises(DownloadError):
            package.get_download_list()
        with open(self.obj_fn) as fp:
            self.assertEqual(fp.read(), content)

    def test_can_download_objects(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        package = Package(dump=self.metadata)
        package.download_objects(self.pkg_uid)
        self.assertTrue(os.path.exists(self.obj_fn))
