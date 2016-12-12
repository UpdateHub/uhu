# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from efu.core.installation_set import InstallationSetMode
from efu.core.package import Package

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
                        'options': {
                            'target-device': '/dev/sda',
                            'target-path': '/boot',
                            'filesystem': 'ext4',
                        }
                    }
                ],
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'options': {
                            'target-device': '/dev/sda',
                            'target-path': '/boot',
                            'filesystem': 'ext4',
                        }
                    }
                ]
            ]
        }))
        pkg = Package.from_file(fn)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.hardwares.all(), self.supported_hardware)
        self.assertEqual(len(pkg.objects.all()), 2)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.options['target-path'], '/boot')
        self.assertEqual(obj.options['filesystem'], 'ext4')

    def test_can_create_package_from_metadata(self):
        metadata = {
            'product': self.product,
            'version': self.version,
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
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
                        'target-device': '/dev/sda',
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
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.options['target-path'], '/boot')
        self.assertEqual(obj.options['filesystem'], 'ext4')

    def test_can_dump_package_with_compression_and_load_from_file(self):
        compressed_fn = os.path.join(
            os.path.dirname(__file__), '../fixtures/compressed/base.txt.gz')

        pkg_fn = self.create_file(b'')
        pkg = Package(InstallationSetMode.ActiveInactive)
        pkg.objects.create(__file__, 'raw', {'target-device': '/'})
        pkg.objects.create(compressed_fn, 'raw', {'target-device': '/'})
        expected = pkg.template(), pkg.metadata()

        pkg.dump(pkg_fn)
        pkg = Package.from_file(pkg_fn)
        observed = pkg.template(), pkg.metadata()
        self.assertEqual(observed, expected)

    def test_can_load_from_metadata_with_compression(self):
        compressed_fn = os.path.join(
            os.path.dirname(__file__), '../fixtures/compressed/base.txt.gz')
        pkg = Package(InstallationSetMode.ActiveInactive)
        pkg.objects.create(compressed_fn, 'raw', {'target-device': '/'})
        pkg.objects.load()
        expected = pkg.metadata()

        pkg = Package.from_metadata(pkg.metadata())
        pkg.objects.load()
        observed = pkg.metadata()
        self.assertEqual(observed, expected)
