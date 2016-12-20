# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from efu.core.package import Package

from . import PackageTestCase


class PackageWithInstallIfDifferentObjectsTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        self.fn = self.create_file(json.dumps({
            'product': '0' * 64,
            'version': '2.0',
            'objects': [
                [
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'target-device': '/dev/sda',
                        'install-condition': 'always',
                    },
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'target-device': '/dev/sda',
                        'install-condition': 'content-diverges'
                    },
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'target-device': '/dev/sda',
                        'install-condition': 'version-diverges',
                        'install-condition-pattern-type': 'u-boot',
                    },
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'target-device': '/dev/sda',
                        'install-condition': 'version-diverges',
                        'install-condition-pattern-type': 'regexp',
                        'install-condition-pattern': '\d+\.\d+',
                    },
                ]
            ]
        }))
        self.metadata = {
            'product': '0' * 64,
            'version': '2.0',
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': 'sha256sum'
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': {
                            'version': '0.1',
                            'pattern': 'linux-kernel',
                        }
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': {
                            'version': '0.1',
                            'pattern': {
                                'regexp': '.+',
                                'seek': 100,
                                'buffer-size': 200,
                            },
                        }
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': {
                            'version': '0.1',
                            'pattern': {'regexp': '.+'},
                        }
                    }
                ]
            ]
        }

    def test_can_load_from_file_always_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj['target-device'], '/dev/sda')
        self.assertEqual(obj['install-condition'], 'always')

    def test_can_load_from_file_content_diverges_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(index=1, installation_set=0)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj['target-device'], '/dev/sda')
        self.assertEqual(obj['install-condition'], 'content-diverges')

    def test_can_load_from_file_known_version_diverges_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(index=2, installation_set=0)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj['target-device'], '/dev/sda')
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'u-boot')

    def test_can_load_from_file_custom_version_diverges_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(index=3, installation_set=0)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj['target-device'], '/dev/sda')
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'regexp')
        self.assertEqual(obj['install-condition-pattern'], '\d+\.\d+')

    def test_can_load_from_metadata_always_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj['install-condition'], 'always')

    def test_can_load_from_metadata_content_diverges_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(index=1, installation_set=0)
        self.assertEqual(obj['install-condition'], 'content-diverges')

    def test_can_load_from_metadata_known_version_diverges_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(index=2, installation_set=0)
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'linux-kernel')

    def test_can_load_from_metadata_custom_version_diverges_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(index=3, installation_set=0)
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'regexp')
        self.assertEqual(obj['install-condition-pattern'], '.+')
        self.assertEqual(obj['install-condition-seek'], 100)
        self.assertEqual(obj['install-condition-buffer-size'], 200)

    def test_can_load_from_metadata_custom_version_object_with_default(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(index=4, installation_set=0)
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'regexp')
        self.assertEqual(obj['install-condition-pattern'], '.+')
        self.assertEqual(obj['install-condition-seek'], 0)
        self.assertEqual(obj['install-condition-buffer-size'], -1)
