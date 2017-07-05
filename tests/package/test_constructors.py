# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os

from uhu.core.objects import InstallationSetMode
from uhu.core.package import Package

from . import PackageTestCase


class PackageConstructorsTestCase(PackageTestCase):

    def test_can_create_package_with_default_constructor(self):
        pkg = Package(
            InstallationSetMode.ActiveInactive, version=self.version,
            product=self.product)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.mode, InstallationSetMode.ActiveInactive)

    def test_can_create_package_from_dumped_file(self):
        fn = self.create_file(json.dumps({
            'product': self.product,
            'version': self.version,
            'supported-hardware': self.supported_hardware,
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'target-type': 'device',
                        'target': '/dev/sda',
                        'target-path': '/boot',
                        'filesystem': 'ext4',
                    }
                ],
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'target-type': 'device',
                        'target': '/dev/sda',
                        'target-path': '/boot',
                        'filesystem': 'ext4',
                    }
                ]
            ]
        }))
        pkg = Package.from_file(fn)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.supported_hardware.all(), self.supported_hardware)
        self.assertEqual(len(pkg.objects.all()), 2)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertEqual(obj['target'], '/dev/sda')
        self.assertEqual(obj['target-path'], '/boot')
        self.assertEqual(obj['filesystem'], 'ext4')

    def test_can_create_package_from_metadata(self):
        metadata = {
            'product': self.product,
            'version': self.version,
            'supported-hardware': 'any',
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-type': 'device',
                        'target': '/dev/sda',
                        'target-path': '/boot',
                        'filesystem': 'ext4'
                    }
                ],
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-type': 'device',
                        'target': '/dev/sda',
                        'target-path': '/boot',
                        'filesystem': 'ext4'
                    }
                ]
            ]
        }
        pkg = Package.from_metadata(metadata)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(len(pkg.objects.all()), 2)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertEqual(obj['target'], '/dev/sda')
        self.assertEqual(obj['target-path'], '/boot')
        self.assertEqual(obj['filesystem'], 'ext4')

    def test_can_dump_package_with_compression_and_load_from_file(self):
        compressed_fn = os.path.join(
            os.path.dirname(__file__), '../fixtures/compressed/base.txt.gz')

        pkg_fn = self.create_file(b'')
        pkg = Package(InstallationSetMode.ActiveInactive)
        pkg.objects.create({
            'filename': __file__,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/'
        })
        pkg.objects.create({
            'filename': compressed_fn,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/'
        })
        expected = pkg.to_template(), pkg.to_metadata()

        pkg.dump(pkg_fn)
        pkg = Package.from_file(pkg_fn)
        observed = pkg.to_template(), pkg.to_metadata()
        self.assertEqual(observed, expected)

    def test_can_load_from_metadata_with_compression(self):
        compressed_fn = os.path.join(
            os.path.dirname(__file__), '../fixtures/compressed/base.txt.gz')
        pkg = Package(InstallationSetMode.ActiveInactive)
        pkg.objects.create({
            'filename': compressed_fn,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/',
        })
        pkg.objects.load()
        expected = pkg.to_metadata()

        pkg = Package.from_metadata(pkg.to_metadata())
        pkg.objects.load()
        observed = pkg.to_metadata()
        self.assertEqual(observed, expected)
