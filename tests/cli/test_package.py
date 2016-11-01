# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from click.testing import CliRunner

from efu.cli.package import (
    add_installation_set_command, remove_installation_set_command,
    add_object_command, edit_object_command, remove_object_command,
    export_command, show_command, new_version_command, status_command,
    set_active_backup_backend)
from efu.core import Package
from efu.utils import LOCAL_CONFIG_VAR, SERVER_URL_VAR


from ..utils import (
    EFUTestCase, FileFixtureMixin, EnvironmentFixtureMixin, HTTPTestCaseMixin)


class PackageTestCase(EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.version = '2.0'
        self.product = '1234'
        self.pkg_fn = self.create_file('')
        self.pkg_uid = '4321'
        self.set_env_var(LOCAL_CONFIG_VAR, self.pkg_fn)
        self.obj_fn = __file__
        self.obj_options = {'target-device': '/dev/sda'}


class SetActiveBackupBackendTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package()
        pkg.dump(self.pkg_fn)

    def test_can_set_active_backup_backend(self):
        pkg = Package.from_file(self.pkg_fn)
        self.assertIsNone(pkg.active_backup_backend)
        result = self.runner.invoke(set_active_backup_backend, ['grub2'])
        self.assertEqual(result.exit_code, 0)
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(pkg.active_backup_backend, 'grub2')

    def test_set_active_backup_backend_returns_2_if_invalid_backend(self):
        pkg = Package.from_file(self.pkg_fn)
        result = self.runner.invoke(set_active_backup_backend, ['invalid'])
        self.assertEqual(result.exit_code, 2)


class AddInstallationSetCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(product=self.product)
        pkg.dump(self.pkg_fn)

    def test_can_add_installation_set(self):
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(len(package.objects), 0)
        result = self.runner.invoke(add_installation_set_command)
        self.assertEqual(result.exit_code, 0)
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(len(package.objects), 1)

    def test_add_installation_set_returns_2_if_adding_more_than_2_sets(self):
        expected = [0, 0, 2]  # 2 succesful runs, 1 with error
        results = []
        for _ in range(3):
            result = self.runner.invoke(add_installation_set_command)
            results.append(result.exit_code)
        self.assertEqual(results, expected)


class RemoveInstallationSetCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(product=self.product)
        pkg.objects.add_list()
        pkg.objects.add_list()
        pkg.dump(self.pkg_fn)

    def test_can_remove_installation_set(self):
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(len(package.objects), 2)
        result = self.runner.invoke(remove_installation_set_command, ['0'])
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(len(package.objects), 1)

    def test_remove_installation_set_returns_2_if_index_is_not_found(self):
        result = self.runner.invoke(remove_installation_set_command, ['10'])
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(len(package.objects), 2)


class AddObjectCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(product=self.product)
        pkg.dump(self.pkg_fn)

    def test_can_add_an_object(self):
        cmd = [self.obj_fn, '-m', 'raw', '-td', '/dev/sda']
        result = self.runner.invoke(add_object_command, cmd)

        self.assertEqual(result.exit_code, 0)
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(len(package.objects), 1)
        obj = package.objects.get(0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_add_command_returns_1_if_package_does_not_exist(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        cmd = [self.obj_fn, '-m', 'raw', '-td', '/dev/sda']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 1)

    def test_cannot_add_object_if_callback_fails(self):
        cmd = [self.obj_fn,
               '-m', 'copy',
               '-td', '/dev/sda',
               '-tp', '/path',
               '-fs', 'ext2',
               '--no-format', 'true',
               '--format-options', 'options']  # requires --format to be true
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 2)

    def test_can_add_a_raw_object_with_all_options(self):
        cmd = [self.obj_fn,
               '--mode', 'raw',
               '--target-device', '/dev/sda',
               '--skip', '128',
               '--count', '-1',
               '--seek', '1234',
               '--chunk-size', '128',
               '--truncate', 'false']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_a_copy_object_with_all_options(self):
        cmd = [self.obj_fn,
               '--mode', 'copy',
               '--target-device', '/dev/sda',
               '--mount-options', 'options',
               '--target-path', '/path',
               '--filesystem', 'ext4',
               '--format', 'true',
               '--format-options', 'options']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_a_tarball_object_with_all_options(self):
        cmd = [self.obj_fn,
               '--mode', 'tarball',
               '--target-device', '/dev/sda',
               '--mount-options', 'options',
               '--target-path', '/path',
               '--filesystem', 'ext4',
               '--format', 'true',
               '--format-options', 'options']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_raw_object_with_only_required_options(self):
        cmd = [self.obj_fn,
               '--mode', 'raw',
               '--target-device', '/dev/sda']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_copy_object_with_only_required_options(self):
        cmd = [self.obj_fn,
               '--mode', 'copy',
               '--target-device', '/dev/sda',
               '--target-path', '/path',
               '--filesystem', 'ext4']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_tarball_object_with_only_required_options(self):
        cmd = [self.obj_fn,
               '--mode', 'tarball',
               '--target-device', '/dev/sda',
               '--target-path', '/path',
               '--filesystem', 'ext4']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_cannot_add_raw_object_without_required_options(self):
        cmd = [self.obj_fn, '--mode', 'raw']
        result = self.runner.invoke(add_object_command, cmd)
        print(result.output)
        self.assertEqual(result.exit_code, 2)

    def test_cannot_add_copy_object_without_required_options(self):
        cmds = (
            [self.obj_fn,
             '--mode', 'copy',
             '--target-device', '/dev/sda',
             '--target-path', '/path'],
            [self.obj_fn,
             '--mode', 'copy',
             '--target-device', '/dev/sda',
             '--filesystem', 'ext4'],
            [self.obj_fn,
             '--mode', 'copy',
             '--target-path', '/path',
             '--filesystem', 'ext4']
        )
        for cmd in cmds:
            result = self.runner.invoke(add_object_command, cmd)
            self.assertEqual(result.exit_code, 2)

    def test_cannot_add_tarball_object_without_required_options(self):
        cmds = (
            [self.obj_fn,
             '--mode', 'tarball',
             '--target-device', '/dev/sda',
             '--target-path', '/path'],
            [self.obj_fn,
             '--mode', 'tarball',
             '--target-device', '/dev/sda',
             '--filesystem', 'ext4'],
            [self.obj_fn,
             '--mode', 'tarball',
             '--target-path', '/path',
             '--filesystem', 'ext4']
        )
        for cmd in cmds:
            result = self.runner.invoke(add_object_command, cmd)
            self.assertEqual(result.exit_code, 2)

    def test_can_add_object_within_specific_index(self):
        self.runner.invoke(add_installation_set_command)
        self.runner.invoke(add_installation_set_command)
        cmd = [self.obj_fn,
               '-m', 'raw',
               '-td', '/dev/sda',
               '--installation-set', '1']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_add_object_within_specific_index_returns_3_if_index_error(self):
        cmd = [self.obj_fn,
               '-m', 'raw',
               '-td', '/dev/sda',
               '--installation-set', '1']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 3)

    def test_add_object_within_specific_index_returns_4_if_missing_index(self):
        self.runner.invoke(add_installation_set_command)
        self.runner.invoke(add_installation_set_command)
        cmd = [self.obj_fn,
               '-m', 'raw',
               '-td', '/dev/sda']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 4)


class EditObjectCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(product=self.product)
        pkg.objects.add_list()
        pkg.objects.add(self.obj_fn, mode='raw', options=self.obj_options)
        pkg.dump(self.pkg_fn)

    def test_can_edit_object_with_edit_object_command(self):
        args = ['0', 'target-device', '/dev/sdb']
        self.runner.invoke(edit_object_command, args=args)
        pkg = Package.from_file(self.pkg_fn)
        obj = pkg.objects.get(0)
        self.assertEqual(obj.options['target-device'], '/dev/sdb')

    def test_edit_command_returns_0_if_successful(self):
        args = ['0', 'target-device', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 0)

    def test_edit_command_returns_1_if_package_does_not_exist(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        args = ['0', 'target-device', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 1)

    def test_edit_command_returns_2_if_object_does_not_exist(self):
        args = ['42', 'target-device', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 2)


class RemoveObjectCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(product=self.product)
        pkg.objects.add_list()
        pkg.objects.add(self.obj_fn, mode='raw', options=self.obj_options)
        pkg.dump(self.pkg_fn)

    def test_can_remove_object_with_remove_command(self):
        self.runner.invoke(
            remove_object_command, args=['0'])
        pkg = Package.from_file(self.pkg_fn)
        self.assertEqual(len(list(pkg.objects.all())), 0)

    def test_remove_command_returns_0_if_successful(self):
        result = self.runner.invoke(
            remove_object_command, args=['0'])
        self.assertEqual(result.exit_code, 0)

    def test_remove_command_returns_1_if_package_does_not_exist(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        result = self.runner.invoke(
            remove_object_command, args=['100'])
        self.assertEqual(result.exit_code, 1)


class ShowCommandTestCase(PackageTestCase):

    def test_show_command_returns_0_if_successful(self):
        pkg = Package(product=self.product)
        pkg.objects.add_list()
        pkg.objects.add(self.obj_fn, mode='raw', options=self.obj_options)
        pkg.dump(self.pkg_fn)
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 0)

    def test_show_command_returns_1_if_package_does_not_exist(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 1)


class ExportCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(product=self.product)
        pkg.objects.add_list()
        pkg.objects.add(self.obj_fn, mode='raw', options=self.obj_options)
        pkg.active_backup_backend = 'grub2'
        pkg.dump(self.pkg_fn)
        self.dest_pkg_fn = '/tmp/pkg-dump'
        self.addCleanup(self.remove_file, self.dest_pkg_fn)

    def test_can_export_package_file(self):
        expected = {
            'product': self.product,
            'version': None,
            'supported-hardware': {},
            'active-backup-backend': 'grub2',
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'compressed': False,
                        'options': {
                            'chunk-size': 131072,
                            'count': -1,
                            'seek': 0,
                            'skip': 0,
                            'target-device': '/dev/sda',
                            'truncate': False
                        }
                    }
                ]
            ]
        }
        self.assertFalse(os.path.exists(self.dest_pkg_fn))
        self.runner.invoke(export_command, args=[self.dest_pkg_fn])
        self.assertTrue(os.path.exists(self.dest_pkg_fn))
        with open(self.dest_pkg_fn) as fp:
            observed = json.load(fp)
        self.assertEqual(observed, expected)

    def test_export_package_command_returns_0_if_successful(self):
        result = self.runner.invoke(
            export_command, args=[self.dest_pkg_fn])
        self.assertEqual(result.exit_code, 0)

    def test_export_command_returns_1_if_package_does_not_exist(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        result = self.runner.invoke(
            export_command, args=[self.dest_pkg_fn])
        self.assertFalse(os.path.exists(self.dest_pkg_fn))
        self.assertEqual(result.exit_code, 1)


class NewVersionCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        Package(product=self.product).dump(self.pkg_fn)

    def test_can_set_package_version(self):
        package = Package.from_file(self.pkg_fn)
        self.assertIsNone(package.version)
        self.runner.invoke(
            new_version_command, args=[self.version])
        package = Package.from_file(self.pkg_fn)
        self.assertEqual(package.version, self.version)

    def test_new_package_version_comands_returns_0_if_successful(self):
        result = self.runner.invoke(
            new_version_command, args=[self.version])
        self.assertEqual(result.exit_code, 0)

    def test_new_package_version_comands_returns_1_without_package_file(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        result = self.runner.invoke(
            new_version_command, args=[self.version])
        self.assertEqual(result.exit_code, 1)


class StatusCommandTestCase(HTTPTestCaseMixin, PackageTestCase):

    def setUp(self):
        super().setUp()
        Package(version=self.version, product=self.product).dump(self.pkg_fn)
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))

    def test_status_command_returns_0_if_successful(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.pkg_uid)
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': 'finished'}))
        result = self.runner.invoke(status_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 0)

    def test_status_command_returns_1_if_package_doesnt_exist(self):
        self.set_env_var(LOCAL_CONFIG_VAR, 'dont-exist')
        result = self.runner.invoke(status_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 1)

    def test_status_command_returns_2_if_status_doesnt_exist(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.pkg_uid)
        self.httpd.register_response(path, status_code=404)
        result = self.runner.invoke(status_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 2)
