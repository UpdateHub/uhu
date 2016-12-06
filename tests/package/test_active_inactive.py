# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.core.installation_set import InstallationSetMode
from efu.core.package import Package

from . import PackageTestCase


class ActiveInactiveTestCase(PackageTestCase):

    def setUp(self):
        self.pkg = Package(InstallationSetMode.ActiveInactive)

    def test_can_set_active_inactive_backend(self):
        self.pkg.active_inactive_backend = 'u-boot'
        self.assertEqual(self.pkg.active_inactive_backend, 'u-boot')
        self.pkg.active_inactive_backend = 'u-boot'
        self.assertEqual(self.pkg.active_inactive_backend, 'u-boot')

    def test_active_inactive_backend_raises_error_if_invalid_backend(self):
        with self.assertRaises(ValueError):
            self.pkg.active_inactive_backend = 'invalid'

    def test_metadata_with_active_inactive_backend(self):
        self.pkg.active_inactive_backend = 'u-boot'
        metadata = self.pkg.metadata()
        self.assertEqual(metadata['active-inactive-backend'], 'u-boot')

    def test_metadata_without_active_inactive_backend(self):
        metadata = self.pkg.metadata()
        self.assertIsNone(metadata.get('active-inactive-backend'))
