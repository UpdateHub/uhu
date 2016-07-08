# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.push import exceptions
from efu.push.file import File
from efu.push.package import Package

from ..base import EFUTestCase


class PackageTestCase(EFUTestCase):

    def test_raises_invalid_package_file_with_inexistent_file(self):
        with self.assertRaises(exceptions.InvalidPackageFileError):
            Package('inexistent_package_file.json')

    def test_raises_invalid_package_file_when_file_is_not_json(self):
        with self.assertRaises(exceptions.InvalidPackageFileError):
            Package(__file__)

    def test_can_load_package_file(self):
        files = [self.create_file(b'0') for _ in range(15)]

        product_id = 1234
        package_fn = self.create_package_file(product_id, files)
        package = Package(package_fn)

        self.assertEqual(package.product_id, product_id)
        self.assertEqual(len(package.files), len(files))
        for file in package.files.values():
            self.assertIsInstance(file, File)

    def test_package_as_dict(self):
        files = [self.create_file(bytes(i)) for i in range(3)]
        package = Package(self.create_package_file(123, files))
        observed = package.as_dict()
        self.assertEqual(len(observed['objects']), len(files))
        for file in observed['objects']:
            self.assertIsNotNone(file['id'])
            self.assertIsNotNone(file['sha256sum'])
