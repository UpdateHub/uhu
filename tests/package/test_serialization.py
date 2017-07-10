# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os
import tarfile
from unittest.mock import patch

from pkgschema import ValidationError

from uhu.core.hardware import SupportedHardwareManager
from uhu.core.objects import ObjectsManager
from uhu.core.package import Package
from uhu.core.utils import dump_package, load_package, dump_package_archive
from uhu.utils import get_local_config_file

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

    def verify_archive(self, dest):
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(tarfile.is_tarfile(dest))

        with tarfile.open(dest) as tar:
            self.assertEqual(len(tar.getmembers()), 2)
            files = tar.getnames()
            member = tar.getmember(self.obj_sha256)
        self.assertIn('metadata', files)
        self.assertIn(self.obj_sha256, files)
        self.assertFalse(member.islnk())
        self.assertFalse(member.issym())

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

    def test_can_archive_package(self):
        pkg = self.create_package()[0]
        expected = '{}-{}.uhupkg'.format(self.product, self.version)
        self.addCleanup(os.remove, expected)
        observed = dump_package_archive(pkg)
        self.assertEqual(expected, observed)
        self.verify_archive(observed)

    def test_dump_package_archive_does_not_archive_links(self):
        pkg = Package(version=self.version, product=self.product)
        expected = '{}-{}.uhupkg'.format(self.product, self.version)

        hlink = 'updatehub_hlink'
        self.addCleanup(os.remove, hlink)
        self.obj_options['filename'] = hlink
        os.symlink(self.obj_fn, hlink)
        pkg.objects.create(self.obj_options)

        slink = 'updatehub_slink'
        self.addCleanup(os.remove, slink)
        self.obj_options['filename'] = slink
        os.link(self.obj_fn, slink)
        pkg.objects.create(self.obj_options)

        self.addCleanup(os.remove, expected)
        observed = dump_package_archive(pkg)
        self.assertEqual(len(pkg.objects.all()), 4)
        self.verify_archive(observed)

    def test_cannot_archive_package_when_output_exists(self):
        pkg = self.create_package()[0]
        output = self.create_file()
        self.assertTrue(os.path.exists(output))
        with self.assertRaises(FileExistsError):
            dump_package_archive(pkg, output)

    def test_can_archive_package_when_output_exists_and_force(self):
        pkg = self.create_package()[0]
        output = self.create_file()
        self.assertTrue(os.path.exists(output))
        dump_package_archive(pkg, output, force=True)
        self.verify_archive(output)

    def test_cannot_archive_package_when_package_misses_info(self):
        invalid_packages = [
            Package(product='1'),  # without version
            Package(version='1'),  # without product UID
            Package(version='1', product='1'),  # without objects
        ]
        output = self.create_file()
        os.remove(output)
        for pkg in invalid_packages:
            with self.assertRaises(ValueError):
                dump_package_archive(pkg, output)

    @patch('uhu.core.utils.pkgschema.validate_metadata',
           side_effect=ValidationError(None))
    def test_cannot_archive_package_when_metadata_is_invalid(self, mock):
        pkg = self.create_package()[0]
        output = self.create_file()
        with self.assertRaises(ValueError):
            dump_package_archive(pkg, output, force=True)
