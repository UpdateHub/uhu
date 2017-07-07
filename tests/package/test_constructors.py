# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from uhu.core.hardware import SupportedHardwareManager
from uhu.core.objects import ObjectsManager
from uhu.core.package import Package

from . import PackageTestCase


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
