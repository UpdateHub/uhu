# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

import click

from efu.core import Object, Package
from efu.utils import LOCAL_CONFIG_VAR

from ..base import (
    PackageMockMixin, BaseTestCase, delete_environment_variable)


class PackageTestCase(PackageMockMixin, BaseTestCase):

    def test_raises_invalid_package_file_with_inexistent_file(self):
        os.environ[LOCAL_CONFIG_VAR] = 'inexistent_package_file.json'
        with self.assertRaises(FileNotFoundError):
            Package(self.version)

    def test_raises_invalid_package_file_when_file_is_not_json(self):
        os.environ[LOCAL_CONFIG_VAR] = __file__
        with self.assertRaises(ValueError):
            Package(self.version)

    def test_can_load_package_file(self):
        files = [self.create_file(b'0') for _ in range(15)]
        id_ = 1234
        os.environ[LOCAL_CONFIG_VAR] = self.create_package_file(
            product=id_, files=files)
        package = Package(self.version)

        self.assertEqual(package.product, id_)
        self.assertEqual(package.version, self.version)
        self.assertEqual(len(package.objects), len(files))
        for file in package.objects.values():
            self.assertIsInstance(file, Object)

    def test_package_serialized(self):
        files = [self.create_file(bytes(i)) for i in range(3)]
        os.environ[LOCAL_CONFIG_VAR] = self.create_package_file(
            product=self.product, files=files)
        observed = Package(self.version).serialize()
        self.assertEqual(observed['version'], self.version)
        self.assertEqual(len(observed['objects']), len(files))
        for file in observed['objects']:
            self.assertIsNotNone(file['id'])
            self.assertIsNotNone(file['sha256sum'])

    def test_package_metadata(self):
        files = [self.create_file(bytes(i)) for i in range(3)]
        os.environ[LOCAL_CONFIG_VAR] = self.create_package_file(
            product=self.product, files=files)
        observed = Package(self.version).metadata.serialize()

        self.assertEqual(observed['product'], self.product)
        self.assertEqual(observed['version'], self.version)
        self.assertEqual(len(observed['images']), len(files))

        for file in observed['images']:
            self.assertIsNotNone(file['sha256sum'])
            self.assertIsNotNone(file['filename'])
            self.assertIsNotNone(file['size'])
