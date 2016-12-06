# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from efu.core.installation_set import InstallationSetMode
from efu.core.package import Package

from . import PackageTestCase


class PackageSupportedHardwareManagementTestCase(PackageTestCase):

    def test_can_add_supported_hardware(self):
        pkg = Package(InstallationSetMode.Single)
        self.assertEqual(len(pkg.supported_hardware), 0)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        self.assertEqual(len(pkg.supported_hardware), 1)
        hardware = pkg.supported_hardware['PowerX']
        self.assertEqual(hardware['name'], 'PowerX')
        self.assertEqual(hardware['revisions'], ['PX230'])

    def test_can_remove_supported_hardware(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware(name='PowerX')
        pkg.add_supported_hardware(name='PowerY')
        self.assertEqual(len(pkg.supported_hardware), 2)
        pkg.remove_supported_hardware('PowerX')
        self.assertEqual(len(pkg.supported_hardware), 1)
        pkg.remove_supported_hardware('PowerY')
        self.assertEqual(len(pkg.supported_hardware), 0)

    def test_remove_supported_hardware_raises_error_if_invalid_hardware(self):
        pkg = Package(InstallationSetMode.Single)
        with self.assertRaises(ValueError):
            pkg.remove_supported_hardware('dosnt-exist')

    def test_can_add_hardware_revision(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        pkg.add_supported_hardware_revision('PowerX', 'PX240')
        revisions = pkg.supported_hardware['PowerX']['revisions']
        self.assertEqual(revisions, ['PX230', 'PX240'])

    def test_add_hardware_revision_raises_error_if_invalid_hardware(self):
        pkg = Package(InstallationSetMode.Single)
        with self.assertRaises(ValueError):
            pkg.add_supported_hardware_revision('dosnt-exist', 'revision')

    def test_can_remove_hardware_revision(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX240'])
        self.assertEqual(len(pkg.supported_hardware['PowerX']['revisions']), 1)
        pkg.remove_supported_hardware_revision('PowerX', 'PX240')
        self.assertEqual(len(pkg.supported_hardware['PowerX']['revisions']), 0)

    def test_remove_hardware_revision_raises_error_if_invalid_hardware(self):
        pkg = Package(InstallationSetMode.Single)
        with self.assertRaises(ValueError):
            pkg.remove_supported_hardware_revision('dosnt-exist', 'revision')

    def test_remove_hardware_revision_raises_error_if_invalid_revision(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware('PowerX')
        with self.assertRaises(ValueError):
            pkg.remove_supported_hardware_revision('PowerX', 'dosnt-exist')

    def test_hardware_revisions_are_alphanumeric_sorted(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX240'])
        pkg.add_supported_hardware_revision('PowerX', 'PX250')
        pkg.add_supported_hardware_revision('PowerX', 'PX230')
        expected = ['PX230', 'PX240', 'PX250']
        observed = pkg.supported_hardware['PowerX']['revisions']
        self.assertEqual(observed, expected)

    def test_entries_are_not_duplicated_when_adding_same_hardware_twice(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        self.assertEqual(len(pkg.supported_hardware), 1)
        self.assertEqual(len(pkg.supported_hardware['PowerX']['revisions']), 1)

    def test_dump_package_with_supported_hardware(self):
        pkg = Package(InstallationSetMode.Single)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        pkg_fn = self.create_file('')
        pkg.dump(pkg_fn)
        with open(pkg_fn) as fp:
            dump = json.load(fp)
        supported_hardware = dump.get('supported-hardware')
        self.assertIsNotNone(supported_hardware)
        self.assertEqual(len(supported_hardware), 1)
        self.assertEqual(supported_hardware['PowerX']['name'], 'PowerX')
        self.assertEqual(supported_hardware['PowerX']['revisions'], ['PX230'])

    def test_supported_hardware_within_package_string(self):
        pkg = Package(
            InstallationSetMode.Single, version='2.0', product='1234')
        pkg.add_supported_hardware(name='PowerX')
        pkg.add_supported_hardware(name='PowerY', revisions=['PY230'])
        pkg.add_supported_hardware(
            name='PowerZ', revisions=['PZ250', 'PZ240', 'PZ230'])
        observed = str(pkg)
        with open('tests/fixtures/supported_hardware.txt') as fp:
            expected = fp.read().strip()
        self.assertEqual(observed, expected)
