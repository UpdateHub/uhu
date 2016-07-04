# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.push import exceptions
from efu.push.file import File
from efu.push.package import Package

from ..base import BasePushTestCase


class PackageTestCase(BasePushTestCase):

    def setUp(self):
        super().setUp()
        self.product_id = 1

    def test_raises_invalid_package_file_with_inexistent_file(self):
        with self.assertRaises(exceptions.InvalidPackageFileError):
            Package('inexistent_package_file.json')

    def test_raises_invalid_package_file_when_file_is_not_json(self):
        with self.assertRaises(exceptions.InvalidPackageFileError):
            Package(__file__)

    def test_can_load_package_file(self):
        files = [self.fixture.create_file(b'0') for _ in range(2)]
        package_fn = self.fixture.set_package(self.product_id, files)

        package = Package(package_fn)

        self.assertEqual(package.product_id, self.product_id)
        self.assertEqual(len(package.files), len(files))
        for file in package.files:
            self.assertIsInstance(file, File)

    def test_file_id_matches_files_index(self):
        files = [self.fixture.create_file(b'0') for _ in range(15)]
        package_fn = self.fixture.set_package(self.product_id, files)
        package = Package(package_fn)

        for file in package.files:
            self.assertEqual(package.files.index(file), file.id)
