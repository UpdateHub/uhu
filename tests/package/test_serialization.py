# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os

from uhu.core.objects import InstallationSetMode
from uhu.core.package import Package

from . import PackageTestCase


class PackageSerializationsTestCase(PackageTestCase):

    def test_can_serialize_package_as_metadata(self):
        pkg = Package(InstallationSetMode.Single, version=self.version,
                      product=self.product)
        pkg.objects.create(self.obj_mode, self.obj_options)
        pkg.supported_hardware.add(self.hardware)
        pkg.objects.load()
        metadata = pkg.metadata()
        self.assertEqual(metadata['version'], self.version)
        self.assertEqual(metadata['product'], self.product)
        # Supported hardware
        self.assertEqual(len(metadata['supported-hardware']), 1)
        self.assertEqual(metadata['supported-hardware'][0], self.hardware)
        # Objects
        objects = metadata['objects']
        self.assertEqual(len(objects), 1)
        obj = objects[0][0]
        self.assertEqual(obj['mode'], self.obj_mode)
        self.assertEqual(obj['filename'], self.obj_fn)
        self.assertEqual(obj['size'], self.obj_size)
        self.assertEqual(obj['sha256sum'], self.obj_sha256)
        self.assertEqual(obj['target'], '/dev/sda')

    def test_can_serialize_package_as_template(self):
        pkg = Package(InstallationSetMode.Single,
                      version=self.version, product=self.product)
        index = pkg.objects.create(self.obj_mode, self.obj_options)
        obj = pkg.objects.get(index=index, installation_set=0)
        expected_obj_template = obj.template()
        pkg.supported_hardware.add(self.hardware)
        template = pkg.template()
        self.assertEqual(template['version'], self.version)
        self.assertEqual(template['product'], self.product)
        self.assertEqual(len(template['objects']), 1)
        self.assertEqual(
            template['supported-hardware'], self.supported_hardware)
        objects = template['objects'][0]
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], expected_obj_template)

    def test_can_serialize_package_as_file(self):
        dest = '/tmp/uhu-dump.json'
        self.addCleanup(self.remove_file, dest)
        pkg = Package(InstallationSetMode.Single,
                      version=self.version, product=self.product)
        index = pkg.objects.create(self.obj_mode, self.obj_options)
        obj = pkg.objects.get(index=index, installation_set=0)
        expected_obj_dump = obj.template()
        self.assertFalse(os.path.exists(dest))
        pkg.dump(dest)
        self.assertTrue(os.path.exists(dest))
        with open(dest) as fp:
            data = fp.read()
            dump = json.loads(data)
        self.assertEqual(data[-1], '\n')
        self.assertEqual(dump['version'], self.version)
        self.assertEqual(dump['product'], self.product)
        self.assertEqual(len(dump['objects']), 1)
        dump_obj = dump['objects'][0][0]
        self.assertEqual(dump_obj, expected_obj_dump)

    def test_can_serialize_package_as_exported_package(self):
        dest = '/tmp/uhu-dump.json'
        self.addCleanup(self.remove_file, dest)
        pkg = Package(InstallationSetMode.ActiveInactive,
                      product=self.product, version=self.version)
        pkg.export(dest)
        with open(dest) as fp:
            exported = json.load(fp)
        self.assertIsNone(exported.get('version'))
        self.assertEqual(exported['product'], self.product)
        self.assertEqual(len(exported['objects']), 2)

    def test_can_serialize_package_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/package/fixtures')
        self.addCleanup(os.chdir, cwd)
        with open('package_full.txt') as fp:
            expected = fp.read()
        package = Package(
            InstallationSetMode.Single, version='2.0',
            product='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')  # nopep8
        package.objects.create('raw', {
            'filename': 'files/pkg.json',
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1234,
            'skip': 0,
            'count': -1
        })
        package.objects.create('raw', {
            'filename': 'files/setup.py',
            'target-type': 'device',
            'target': '/dev/sda',
            'seek': 5,
            'truncate': True,
            'chunk-size': 10000,
            'skip': 19,
            'count': 3
        })
        package.objects.create('copy', {
            'filename': 'files/tox.ini',
            'target-type': 'device',
            'target': '/dev/sda3',
            'target-path': '/dev/null',
            'filesystem': 'ext4',
            'format?': True,
            'format-options': '-i 100 -J size=500',
            'mount-options': '--all --fstab=/etc/fstab2'
        })
        package.objects.create('tarball', {
            'filename': 'files/archive.tar.gz',
            'target-type': 'device',
            'target': '/dev/sda3',
            'target-path': '/dev/null',
            'filesystem': 'ext4',
            'format?': True,
            'format-options': '-i 100 -J size=500',
            'mount-options': '--all --fstab=/etc/fstab2'
        })
        self.assertEqual(str(package), expected)

    def test_package_as_string_when_empty(self):
        cwd = os.getcwd()
        os.chdir('tests/package/fixtures')
        self.addCleanup(os.chdir, cwd)
        pkg = Package(InstallationSetMode.Single)
        observed = str(pkg)
        with open('package_empty.txt') as fp:
            expected = fp.read().strip()
        self.assertEqual(observed, expected)
