# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import base64
import hashlib
import os
import zipfile
import unittest
from unittest.mock import patch

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from pkgschema import ValidationError

from uhu.core.hardware import SupportedHardwareManager
from uhu.core.objects import ObjectsManager
from uhu.core.package import Package
from uhu.core.utils import dump_package, load_package, dump_package_archive
from uhu.utils import CHUNK_SIZE_VAR, PRIVATE_KEY_FN

from utils import FileFixtureMixin, EnvironmentFixtureMixin, UHUTestCase


class PackageTestCase(FileFixtureMixin, EnvironmentFixtureMixin, UHUTestCase):

    def setUp(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        self.private_key = RSA.generate(1024)
        private_key_path = self.create_file(self.private_key.exportKey())
        self.set_env_var(PRIVATE_KEY_FN, private_key_path)

        self.version = '2.0'
        self.product = 'a' * 64
        self.hardware = 'PowerX'
        self.pkg_uid = 'pkg-uid'
        content = b'spam'
        self.obj_fn = self.create_file(content, name='object')
        self.obj_sha256 = hashlib.sha256(content).hexdigest()
        self.obj_options = {
            'filename': self.obj_fn,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
        }


class PackageConstructorsTestCase(PackageTestCase):

    def test_can_create_package(self):
        pkg = Package(version=self.version, product=self.product)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.objects, ObjectsManager())
        self.assertEqual(pkg.supported_hardware, SupportedHardwareManager())

    def test_can_create_package_from_dump(self):
        dump = {
            'product': self.product,
            'version': self.version,
        }

        # Supported hardware
        hardware_dump = {'supported-hardware': 'any'}
        dump.update(hardware_dump)
        hardware = SupportedHardwareManager(dump=hardware_dump)

        # Objects
        object_dump = {
            'filename': self.obj_fn,
            'mode': 'copy',
            'target-type': 'device',
            'target': '/dev/sda',
            'target-path': '/boot',
            'filesystem': 'ext4',
        }
        objects_dump = {'objects': [[object_dump], [object_dump]]}
        dump.update(objects_dump)
        objects = ObjectsManager(dump=objects_dump)

        pkg = Package(dump=dump)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.supported_hardware, hardware)
        self.assertEqual(pkg.objects, objects)


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
        self.assertTrue(zipfile.is_zipfile(dest))

        with zipfile.ZipFile(dest) as archive:
            files = archive.namelist()
            member = archive.extract(self.obj_sha256)
            sig_fn = archive.extract('signature')
            metadata_fn = archive.extract('metadata')
            self.addCleanup(os.remove, member)
            self.addCleanup(os.remove, sig_fn)
            self.addCleanup(os.remove, metadata_fn)

        self.assertEqual(len(files), 3)
        self.assertIn(self.obj_sha256, files)
        self.assertFalse(os.path.islink(member))

        with open(metadata_fn) as fp:
            message = SHA256.new(fp.read().encode())
        with open(sig_fn) as fp:
            signature = base64.b64decode(fp.read())
        verifier = PKCS1_v1_5.new(self.private_key)
        self.assertTrue(verifier.verify(message, signature))

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
        os.chdir('tests/core/fixtures')
        self.addCleanup(os.chdir, cwd)
        expected = self.read_file('package_string.txt')
        pkg = self.create_package()[0]
        self.assertEqual(str(pkg), expected)

    def test_package_as_string_when_empty(self):
        cwd = os.getcwd()
        os.chdir('tests/core/fixtures')
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

    def test_can_archive_package_with_force(self):
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


class PackagePushTestCase(unittest.TestCase):

    @patch('uhu.core.package.push_package', return_value='42')
    def test_push_sets_package_uid_when_successful(self, mock):
        pkg = Package()
        uid = pkg.push()
        self.assertEqual(pkg.uid, '42')
        self.assertEqual(uid, '42')
