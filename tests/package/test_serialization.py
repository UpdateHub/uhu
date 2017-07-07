# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os

from uhu.core.hardware import SupportedHardwareManager
from uhu.core.objects import ObjectsManager
from uhu.core.package import Package
from uhu.core.utils import dump_package, load_package

from . import PackageTestCase


class PackageSerializationTestCase(PackageTestCase):

    def create_package(self):
        pkg = Package(version=self.version, product=self.product)
        pkg.objects.create(self.obj_options)
        pkg.supported_hardware.add(self.hardware)
        # control supported hardware
        hw = SupportedHardwareManager()
        hw.add(self.hardware)
        # control objects
        objs = ObjectsManager()
        objs.create(self.obj_options)
        return pkg, hw, objs

    def test_can_serialize_package_as_metadata(self):
        pkg, hw, objs = self.create_package()
        pkg.objects.load()
        metadata = pkg.to_metadata()

        self.assertEqual(metadata['version'], self.version)
        self.assertEqual(metadata['product'], self.product)
        self.assertEqual(metadata[hw.metadata], hw.to_metadata()[hw.metadata])
        self.assertEqual(
            metadata[objs.metadata], objs.to_metadata()[objs.metadata])

    def test_can_serialize_package_as_template_with_version(self):
        pkg, hw, objs = self.create_package()
        template = pkg.to_template()

        self.assertEqual(template['version'], self.version)
        self.assertEqual(template['product'], self.product)
        self.assertEqual(template[hw.metadata], hw.to_template()[hw.metadata])
        self.assertEqual(
            template[objs.metadata], objs.to_template()[objs.metadata])

    def test_can_serialize_package_as_template_without_version(self):
        pkg, hw, objs = self.create_package()
        template = pkg.to_template(with_version=False)

        self.assertIsNone(template['version'], None)
        self.assertEqual(template['product'], self.product)
        self.assertEqual(template[hw.metadata], hw.to_template()[hw.metadata])
        self.assertEqual(
            template[objs.metadata], objs.to_template()[objs.metadata])

    def test_can_dump_and_load_package_from_file(self):
        pkg_fn = '/tmp/uhu-dump.json'
        self.addCleanup(self.remove_file, pkg_fn)
        self.assertFalse(os.path.exists(pkg_fn))
        pkg, hw, objs = self.create_package()

        # dump
        dump_package(pkg.to_template(), pkg_fn)
        self.assertTrue(os.path.exists(pkg_fn))

        # load
        new_pkg = load_package(pkg_fn)
        template = new_pkg.to_template()
        self.assertEqual(template['version'], self.version)
        self.assertEqual(template['product'], self.product)
        self.assertEqual(template[hw.metadata], hw.to_template()[hw.metadata])
        self.assertEqual(
            template[objs.metadata], objs.to_template()[objs.metadata])

    def test_can_serialize_package_as_string(self):
        self.maxDiff = None
        cwd = os.getcwd()
        os.chdir('tests/package/fixtures')
        self.addCleanup(os.chdir, cwd)
        expected = self.read_file('package_string.txt')
        pkg = self.create_package()[0]
        self.assertEqual(str(pkg), expected)

    def test_package_as_string_when_empty(self):
        cwd = os.getcwd()
        os.chdir('tests/package/fixtures')
        self.addCleanup(os.chdir, cwd)
        expected = self.read_file('package_string_empty.txt')
        pkg = Package()
        self.assertEqual(str(pkg), expected)
