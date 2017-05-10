# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.core.package import Package
from efu.core.manager import InstallationSetMode
from efu.repl.repl import EFURepl
from efu.utils import LOCAL_CONFIG_VAR

from utils import EFUTestCase, EnvironmentFixtureMixin, FileFixtureMixin


class EFUReplTestCase(EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def test_can_create_repl_with_default_package(self):
        pkg_fn = self.create_file(b'')
        self.set_env_var(LOCAL_CONFIG_VAR, pkg_fn)
        pkg = Package(InstallationSetMode.ActiveInactive, version='2.0')
        pkg.dump(pkg_fn)
        repl = EFURepl()
        self.assertEqual(repl.package.version, '2.0')

    def test_cannot_start_with_invalid_package_file(self):
        self.set_env_var(LOCAL_CONFIG_VAR, self.create_file(b''))
        with self.assertRaises(SystemExit):
            repl = EFURepl()

    def test_can_create_repl_with_custom_package_file(self):
        pkg_fn = self.create_file(b'')
        pkg = Package(InstallationSetMode.ActiveInactive, version='2.0')
        pkg.dump(pkg_fn)
        repl = EFURepl(pkg_fn)
        self.assertEqual(repl.package.version, '2.0')

    def test_cannot_start_with_invalid_custom_package_file(self):
        pkg_fn = self.create_file(b'')
        with self.assertRaises(SystemExit):
            repl = EFURepl(pkg_fn)

    def test_can_start_a_new_package(self):
        repl = EFURepl()
        self.assertIsNone(repl.package.version)
        self.assertIsNone(repl.package.product)
        self.assertEqual(len(repl.package.objects.all()), 0)
