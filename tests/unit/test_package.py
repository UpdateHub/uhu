# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import shutil
import unittest

import click

from efu.core import Object, Package
from efu.utils import LOCAL_CONFIG_VAR

from ..base import (
    PackageMockMixin, BaseTestCase, HTTPServerMockMixin,
    delete_environment_variable)


class PackageTestCase(PackageMockMixin, BaseTestCase):

    def test_raises_invalid_package_file_with_inexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            Package.from_file('inexistent_package_file.json')

    def test_raises_error_when_file_is_not_json(self):
        with self.assertRaises(ValueError):
            Package().from_file(__file__)

    def test_can_load_package_file(self):
        files = [self.create_file(b'0') for _ in range(1)]
        pkg_file = self.create_package_file(
            version=self.version, files=files, product=self.product)
        package = Package.from_file(pkg_file)
        self.assertEqual(package.product, self.product)
        self.assertEqual(package.version, self.version)
        self.assertEqual(len(package.objects), len(files))
        for obj in package.objects.values():
            self.assertIsInstance(obj, Object)

    def test_package_serialized(self):
        objects = [self.create_file(bytes(i)) for i in range(3)]
        pkg_file = self.create_package_file(
            product=self.product, files=objects, version=self.version)
        package = Package.from_file(pkg_file)
        observed = package.serialize()

        self.assertEqual(observed['version'], self.version)
        self.assertEqual(len(observed['objects']), len(objects))
        for file in observed['objects']:
            self.assertIsNotNone(file['sha256sum'])

    def test_package_metadata(self):
        objects = [self.create_file(bytes(i)) for i in range(3)]
        pkg_file = self.create_package_file(
            product=self.product, files=objects, version=self.version)
        package = Package.from_file(pkg_file)
        observed = package.metadata.serialize()

        self.assertEqual(observed['product'], self.product)
        self.assertEqual(observed['version'], self.version)
        self.assertEqual(len(observed['objects']), len(objects))

        for file in observed['objects']:
            self.assertIsNotNone(file['sha256sum'])
            self.assertIsNotNone(file['filename'])
            self.assertIsNotNone(file['size'])

    def test_can_dump_a_package(self):
        expected = {
            'product': self.product,
            'version': None,
            'objects': {
                '1': {
                    'filename': __file__,
                    'mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        dest_fn = '/tmp/efu-dumped'
        self.addCleanup(self.remove_file, dest_fn)
        pkg_file = self.create_package_file(
            self.version, [__file__], self.product)
        package = Package.from_file(pkg_file)

        self.assertFalse(os.path.exists(dest_fn))
        package.dump(dest_fn)
        self.assertTrue(os.path.exists(dest_fn))

        with open(dest_fn) as fp:
            dumped_package = json.load(fp)
        self.assertEqual(dumped_package, expected)

    def test_can_dump_a_package_with_version(self):
        expected = {
            'product': self.product,
            'version': self.version,
            'objects': {
                '1': {
                    'filename': __file__,
                    'mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        dest_fn = '/tmp/efu-dumped'
        self.addCleanup(self.remove_file, dest_fn)
        pkg_file = self.create_package_file(
            self.version, [__file__], self.product)
        package = Package.from_file(pkg_file)
        package.dump(dest_fn, full=True)
        self.assertTrue(os.path.exists(dest_fn))
        with open(dest_fn) as fp:
            dumped_package = json.load(fp)
        self.assertEqual(dumped_package, expected)

    def test_package_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/unit/fixtures')
        self.addCleanup(os.chdir, cwd)

        pkg_file = self.create_file(b'')
        shutil.copyfile('local_config.json', pkg_file)
        with open('local_config.txt') as fp:
            expected = fp.read().strip()
        package = Package.from_file(pkg_file)
        observed = str(package)
        self.assertEqual(observed, expected)

    def test_can_add_an_object(self):
        pkg_file = self.create_package_file(
            product=self.product, files=[], version=self.version)
        package = Package.from_file(pkg_file)
        obj_fn = self.create_file(b'')
        options = {
            'filename': obj_fn,
            'mode': 'raw',
            'target-device': '/dev/sda'
        }
        self.assertEqual(len(package.objects), 0)
        package.add_object(obj_fn, options)
        self.assertEqual(len(package.objects), 1)
        obj = package.objects.get(1)
        self.assertIsInstance(obj, Object)
        self.assertEqual(obj.filename, obj_fn)
        self.assertEqual(obj.metadata.mode, 'raw')
        self.assertEqual(obj.metadata.target_device, '/dev/sda')

    def test_can_add_more_than_one_object_per_file(self):
        package = Package()
        obj = self.create_file(b'')
        package.add_object(obj, {})
        package.add_object(obj, {})
        self.assertEqual(len(package.objects), 2)

    def test_can_edit_object(self):
        obj = self.create_file(b'123')
        pkg_file = self.create_package_file(
            product=self.product, files=[obj], version=self.version)
        package = Package.from_file(pkg_file)
        pkg_obj = package.objects[1]
        self.assertEqual(pkg_obj.options['target-device'], 'device')
        package.edit_object(1, 'target-device', '/dev/sdb')
        self.assertEqual(pkg_obj.options['target-device'], '/dev/sdb')

    def test_can_remove_object(self):
        objects = [self.create_file(bytes(i)) for i in range(3)]
        obj = 1
        pkg_file = self.create_package_file(
            product=self.product, files=objects, version=self.version)
        package = Package.from_file(pkg_file)

        self.assertIsNotNone(package.objects.get(obj))
        self.assertEqual(len(package.objects), 3)

        package.remove_object(obj)

        self.assertIsNone(package.objects.get(obj))
        self.assertEqual(len(package.objects), 2)

    def test_remove_object_does_nothing_if_object_doesnt_exist(self):
        objects = [self.create_file(bytes(i)) for i in range(3)]
        pkg_file = self.create_package_file(
            product=self.product, files=objects, version=self.version)
        package = Package.from_file(pkg_file)

        self.assertEqual(len(package.objects), 3)
        package.remove_object('no-exists')
        self.assertEqual(len(package.objects), 3)

    def test_can_create_package_file_from_metadata(self):
        cwd = os.getcwd()
        os.chdir('tests/unit/fixtures')
        self.addCleanup(os.chdir, cwd)
        with open('metadata.json') as fp:
            metadata = json.load(fp)
        package = Package.from_metadata(metadata)
        self.assertIsNone(package.version)
        self.assertEqual(package.product, metadata['product'])
        self.assertEqual(len(package.objects), len(metadata['objects']))


class PackageStatusTestCase(
        PackageMockMixin, HTTPServerMockMixin, BaseTestCase):

    def test_can_get_a_package_status(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.package_id)
        expected = 'finished'
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': expected}))
        observed = Package.get_status(self.product, self.package_id)
        self.assertEqual(observed, expected)

    def test_get_package_status_raises_error_if_package_doesnt_exist(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.package_id)
        self.httpd.register_response(path, status_code=404)
        with self.assertRaises(ValueError):
            Package.get_status(self.product, self.package_id)
