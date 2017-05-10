# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

from uhu.cli.hardware import (
    add_supported_hardware_command, remove_supported_hardware_command)
from uhu.core import Package
from uhu.core.manager import InstallationSetMode

from cli.test_package import PackageTestCase


class SupportedHardwareCommandsTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        self.pkg = Package(InstallationSetMode.Single)
        self.pkg.dump(self.pkg_fn)

    def test_can_add_supported_hardware_without_revisions(self):
        result = self.runner.invoke(
            add_supported_hardware_command, args=['PowerX'])
        self.assertEqual(result.exit_code, 0)
        pkg = Package.from_file(self.pkg_fn)
        hardware = pkg.hardwares.get('PowerX')
        self.assertIsNotNone(hardware)
        self.assertEqual(hardware['name'], 'PowerX')
        self.assertEqual(len(hardware['revisions']), 0)

    def test_can_add_supported_hardware_with_revisions(self):
        result = self.runner.invoke(
            add_supported_hardware_command, args=[
                'PowerX',
                '--revision', '3',
                '-r', '2',
                '-r', '1'])
        self.assertEqual(result.exit_code, 0)
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(pkg.hardwares.count(), 1)
        hardware = pkg.hardwares.get('PowerX')
        self.assertEqual(hardware['name'], 'PowerX')
        self.assertEqual(hardware['revisions'], ['1', '2', '3'])

    def test_can_add_supported_hardware_revision(self):
        self.pkg.hardwares.add('PowerX', revisions=['2'])
        self.pkg.dump(self.pkg_fn)
        result = self.runner.invoke(add_supported_hardware_command, args=[
            'PowerX',
            '--revision', '1'])
        self.assertEqual(result.exit_code, 0)
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(pkg.hardwares.count(), 1)
        hardware = pkg.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 2)
        self.assertEqual(hardware['revisions'], ['1', '2'])

    def test_remove_supported_hardware_returns_2_if_hardware_is_invalid(self):
        self.pkg.hardwares.add('PowerX', revisions=['exists'])
        self.pkg.dump(self.pkg_fn)
        result = self.runner.invoke(
            remove_supported_hardware_command, args=[
                'PowerX', '-r', 'no-exists'])
        self.assertEqual(result.exit_code, 2)

    def test_remove_supported_hardware_returns_2_if_revision_is_invalid(self):
        result = self.runner.invoke(
            remove_supported_hardware_command, args=['PowerX'])
        self.assertEqual(result.exit_code, 2)

    def test_can_remove_supported_hardware(self):
        self.pkg.hardwares.add('PowerX')
        self.pkg.dump(self.pkg_fn)
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(pkg.hardwares.count(), 1)
        result = self.runner.invoke(
            remove_supported_hardware_command, args=['PowerX'])
        self.assertEqual(result.exit_code, 0)
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(pkg.hardwares.count(), 0)

    def test_can_remove_supported_hardware_revision(self):
        self.pkg.hardwares.add('PowerX', revisions=['3', '2', '1'])
        self.pkg.dump(self.pkg_fn)
        self.runner.invoke(remove_supported_hardware_command, args=[
            'PowerX',
            '-r', '2'
        ])
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(pkg.hardwares.count(), 1)
        hardware = pkg.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 2)
        self.assertNotIn('2', hardware['revisions'])
        self.assertEqual(hardware['revisions'], ['1', '3'])
