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
        with self.assertRaises(FileNotFoundError):
            Package.from_file('inexistent_package_file.json')

    def test_raises_error_when_file_is_not_json(self):
        with self.assertRaises(ValueError):
            Package().from_file(__file__)

    def test_can_load_package_file(self):
        objects = [self.create_file(b'0') for _ in range(15)]
        pkg_file = self.create_package_file(
            version=self.version, product=self.product, objects=objects)
        package = Package.from_file(pkg_file)

        self.assertEqual(package.product, self.product)
        self.assertEqual(package.version, self.version)
        self.assertEqual(len(package.objects), len(objects))
        for obj in package.objects.values():
            self.assertIsInstance(obj, Object)

    def test_package_serialized(self):
        objects = [self.create_file(bytes(i)) for i in range(3)]
        pkg_file = self.create_package_file(
            product=self.product, objects=objects, version=self.version)
        package = Package.from_file(pkg_file)
        observed = package.serialize()

        self.assertEqual(observed['version'], self.version)
        self.assertEqual(len(observed['objects']), len(objects))
        for file in observed['objects']:
            self.assertIsNotNone(file['id'])
            self.assertIsNotNone(file['sha256sum'])

    def test_package_metadata(self):
        objects = [self.create_file(bytes(i)) for i in range(3)]
        pkg_file = self.create_package_file(
            product=self.product, objects=objects, version=self.version)
        package = Package.from_file(pkg_file)
        observed = package.metadata.serialize()

        self.assertEqual(observed['product'], self.product)
        self.assertEqual(observed['version'], self.version)
        self.assertEqual(len(observed['images']), len(objects))

        for file in observed['images']:
            self.assertIsNotNone(file['sha256sum'])
            self.assertIsNotNone(file['filename'])
            self.assertIsNotNone(file['size'])
