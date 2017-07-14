# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os
import unittest
from unittest.mock import Mock, patch

from click.testing import CliRunner

from uhu.cli.package import (
    add_object_command, edit_object_command, remove_object_command,
    archive_command, export_command, show_command, set_version_command,
    status_command, metadata_command)
from uhu.cli.utils import open_package
from uhu.core.package import Package
from uhu.core.utils import dump_package, load_package
from uhu.core.updatehub import UpdateHubError
from uhu.utils import LOCAL_CONFIG_VAR, SERVER_URL_VAR


from utils import UHUTestCase, FileFixtureMixin, EnvironmentFixtureMixin


class PackageTestCase(EnvironmentFixtureMixin, FileFixtureMixin, UHUTestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.version = '2.0'
        self.product = '1234'
        self.pkg_fn = self.create_file('')
        self.pkg_uid = '4321'
        self.set_env_var(LOCAL_CONFIG_VAR, self.pkg_fn)
        self.obj_fn = __file__
        self.obj_options = {
            'filename': self.obj_fn,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
        }


class AddObjectCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package()
        dump_package(pkg.to_template(), self.pkg_fn)

    def test_can_add_object(self):
        cmd = [self.obj_fn, '-m', 'raw', '-t', '/dev/sda', '-tt', 'device']
        result = self.runner.invoke(add_object_command, cmd)

        self.assertEqual(result.exit_code, 0)
        package = load_package(self.pkg_fn)
        obj = package.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj['target'], '/dev/sda')

    def test_cannot_add_object_if_callback_fails(self):
        cmd = [self.obj_fn,
               '-m', 'copy',
               '-tt', '/dev/sda',
               '-t', '/dev/sda',
               '-tp', '/path',
               '-fs', 'ext2',
               '--no-format', 'true',
               '--format-options', 'options']  # requires --format to be true
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 2)

    def test_can_add_a_raw_object_with_all_options(self):
        cmd = [self.obj_fn,
               '--mode', 'raw',
               '--target-type', 'device',
               '--target', '/dev/sda',
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
               '--target-type', 'device',
               '--target', '/dev/sda',
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
               '--target-type', 'device',
               '--target', '/dev/sda',
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
               '--target-type', 'device',
               '--target', '/dev/sda']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_copy_object_with_only_required_options(self):
        cmd = [self.obj_fn,
               '--mode', 'copy',
               '--target-type', 'device',
               '--target', '/dev/sda',
               '--target-path', '/path',
               '--filesystem', 'ext4']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_tarball_object_with_only_required_options(self):
        cmd = [self.obj_fn,
               '--mode', 'tarball',
               '--target-type', 'device',
               '--target', '/dev/sda',
               '--target-path', '/path',
               '--filesystem', 'ext4']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_cannot_add_raw_object_without_required_options(self):
        cmd = [self.obj_fn, '--mode', 'raw']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 2)

    def test_cannot_add_copy_object_without_required_options(self):
        cmds = (
            [self.obj_fn,
             '--mode', 'copy',
             '--target-type', 'device',
             '--target', '/dev/sda',
             '--target-path', '/path'],
            [self.obj_fn,
             '--mode', 'copy',
             '--target-type', 'device',
             '--target', '/dev/sda',
             '--filesystem', 'ext4'],
            [self.obj_fn,
             '--mode', 'copy',
             '--target-type', 'device',
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
             '--target-type', 'device',
             '--target', '/dev/sda',
             '--target-path', '/path'],
            [self.obj_fn,
             '--mode', 'tarball',
             '--target-type', 'device',
             '--target', '/dev/sda',
             '--filesystem', 'ext4'],
            [self.obj_fn,
             '--mode', 'tarball',
             '--target-type', 'device',
             '--target-path', '/path',
             '--filesystem', 'ext4']
        )
        for cmd in cmds:
            result = self.runner.invoke(add_object_command, cmd)
            self.assertEqual(result.exit_code, 2)


class ArchiveCommand(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package()
        pkg.objects.create(self.obj_options)
        dump_package(pkg.to_template(), self.pkg_fn)

    @patch('uhu.cli.package.dump_package_archive')
    def test_can_archive_with_default_options(self, mock):
        result = self.runner.invoke(archive_command)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock.call_count, 1)
        _, output, force = mock.call_args[0]
        self.assertIsNone(output)
        self.assertFalse(force)

    @patch('uhu.cli.package.dump_package_archive')
    def test_can_archive_with_custom_options(self, mock):
        result = self.runner.invoke(
            archive_command, ['--force', '--output', 'spam'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock.call_count, 1)
        _, output, force = mock.call_args[0]
        self.assertEqual(output, 'spam')
        self.assertTrue(force)

    @patch('uhu.cli.package.dump_package_archive', side_effect=FileExistsError)
    def test_archive_command_returns_1_if_archive_exists(self, mock):
        result = self.runner.invoke(archive_command)
        self.assertEqual(result.exit_code, 1)

    @patch('uhu.cli.package.dump_package_archive', side_effect=ValueError)
    def test_archive_command_returns_2_if_package_is_invalid(self, mock):
        result = self.runner.invoke(archive_command)
        self.assertEqual(result.exit_code, 2)


class EditObjectCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package()
        pkg.objects.create(self.obj_options)
        dump_package(pkg.to_template(), self.pkg_fn)

    def test_can_edit_object_with_edit_object_command(self):
        args = [
            '--index', '0',
            '--installation-set', '0',
            '--option', 'target',
            '--value', '/dev/sdb']
        self.runner.invoke(edit_object_command, args=args)
        pkg = load_package(self.pkg_fn)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj['target'], '/dev/sdb')

    def test_can_edit_object_filename_with_edit_object_command(self):
        args = [
            '--index', '0',
            '--option', 'filename',
            '--value', self.pkg_fn]
        self.runner.invoke(edit_object_command, args=args)
        pkg = load_package(self.pkg_fn)
        obj = pkg.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.filename, self.pkg_fn)

    def test_edit_command_returns_0_if_successful(self):
        args = [
            '--index', '0',
            '--installation-set', '0',
            '--option', 'target',
            '--value', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 0)

    def test_edit_command_returns_2_if_object_does_not_exist(self):
        args = ['42', 'target', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 2)

    def test_edit_command_returns_3_if_validation_error(self):
        args = [
            '--index', '0',
            '--installation-set', '0',
            '--option', 'target-path',
            '--value', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 3)


class RemoveObjectCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package()
        pkg.objects.create(self.obj_options)
        dump_package(pkg.to_template(), self.pkg_fn)

    def test_can_remove_object_with_remove_command(self):
        self.runner.invoke(
            remove_object_command, args=['0'])
        pkg = load_package(self.pkg_fn)
        self.assertEqual(len(pkg.objects.all()), 0)

    def test_remove_command_returns_0_if_successful(self):
        result = self.runner.invoke(
            remove_object_command, args=['0'])
        self.assertEqual(result.exit_code, 0)


class ShowCommandTestCase(PackageTestCase):

    def test_show_command_returns_0_if_successful(self):
        pkg = Package()
        pkg.objects.create(self.obj_options)
        dump_package(pkg.to_template(), self.pkg_fn)
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 0)


class ExportCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        pkg = Package(version='1.0')
        pkg.objects.create(self.obj_options)
        dump_package(pkg.to_template(), self.pkg_fn)
        self.dest_pkg_fn = '/tmp/pkg-dump'
        self.addCleanup(self.remove_file, self.dest_pkg_fn)

    def test_can_export_package_file(self):
        obj = {
            'filename': self.obj_fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'install-condition': 'always',
        }
        expected = {
            'product': None,
            'version': None,
            'supported-hardware': 'any',
            'objects': [[obj], [obj]],
        }
        self.assertFalse(os.path.exists(self.dest_pkg_fn))
        self.runner.invoke(export_command, args=[self.dest_pkg_fn])
        self.assertTrue(os.path.exists(self.dest_pkg_fn))
        with open(self.dest_pkg_fn) as fp:
            observed = json.load(fp)
        print(observed)
        self.assertEqual(observed, expected)

    def test_export_package_command_returns_0_if_successful(self):
        result = self.runner.invoke(
            export_command, args=[self.dest_pkg_fn])
        self.assertEqual(result.exit_code, 0)


class SetVersionCommandTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        dump_package(Package().to_template(), self.pkg_fn)

    def test_can_set_package_version(self):
        package = load_package(self.pkg_fn)
        self.assertIsNone(package.version)
        self.runner.invoke(
            set_version_command, args=[self.version])
        package = load_package(self.pkg_fn)
        self.assertEqual(package.version, self.version)

    def test_new_package_version_comands_returns_0_if_successful(self):
        result = self.runner.invoke(
            set_version_command, args=[self.version])
        self.assertEqual(result.exit_code, 0)


class PackageStatusCommandTestCase(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch('uhu.cli.package.open_package')
    @patch('uhu.cli.package.get_package_status', return_value='Done')
    def test_returns_0_if_successful(self, mock, open_package):
        open_package.return_value.__enter__.return_value = Mock()
        result = self.runner.invoke(status_command, args=['pkg_uid'])
        self.assertEqual(result.exit_code, 0)

    @patch('uhu.cli.package.open_package')
    @patch('uhu.cli.package.get_package_status', side_effect=UpdateHubError)
    def test_returns_2_if_fail(self, mock, open_package):
        result = self.runner.invoke(status_command, args=['pkg_uid'])
        self.assertEqual(result.exit_code, 2)


class UtilsTestCase(FileFixtureMixin, EnvironmentFixtureMixin, UHUTestCase):

    def test_open_package_quits_program_if_invalid_package(self):
        pkg_fn = self.create_file(b'')
        self.set_env_var(LOCAL_CONFIG_VAR, pkg_fn)

        pkg = Package()
        template = pkg.to_template()
        del template['objects']
        with open(pkg_fn, 'w') as fp:
            json.dump(template, fp)

        with self.assertRaises(SystemExit):
            with open_package() as pkg:
                pass


class MetadataTestCase(PackageTestCase):

    def test_metadata_commands_returns_0_when_metadata_is_valid(self):
        pkg = Package()
        pkg.objects.create(self.obj_options)
        pkg.product = '0' * 64
        pkg.version = '2.0'
        dump_package(pkg.to_template(), self.pkg_fn)
        result = self.runner.invoke(metadata_command)
        self.assertEqual(result.exit_code, 0)

    def test_metadata_commands_returns_1_when_metadata_is_invalid(self):
        pkg = Package()
        dump_package(pkg.to_template(), self.pkg_fn)
        result = self.runner.invoke(metadata_command)
        self.assertEqual(result.exit_code, 1)
