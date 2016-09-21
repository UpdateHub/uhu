# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest

import click
from click.testing import CliRunner

import efu.cli.package
from efu.cli.package import (
    add_object_command, edit_object_command, export_command,
    new_version_command, remove_object_command, status_command, show_command)
from efu.utils import LOCAL_CONFIG_VAR
from efu.core import Package

from ..base import (
    PackageMockMixin, BaseTestCase, HTTPServerMockMixin,
    delete_environment_variable)


class AddObjectCommandTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.pkg_file = self.create_package_file(
            self.version, [], self.product)
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.runner = CliRunner()

    def test_can_add_an_object(self):
        package = Package.from_file(self.pkg_file)
        self.assertIsNone(package.objects.get(__file__))

        cmd = [__file__, '-m', 'raw', '-td', 'device']
        result = self.runner.invoke(add_object_command, cmd)

        self.assertEqual(result.exit_code, 0)
        package = Package.from_file(self.pkg_file)
        self.assertEqual(len(package.objects), 1)
        obj = package.objects.get(1)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.metadata.mode, 'raw')
        self.assertEqual(obj.metadata.target_device, 'device')

    def test_export_command_returns_1_if_package_does_not_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = 'dont-exist'
        cmd = [__file__, '-m', 'raw', '-td', 'device']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 1)

    def test_cannot_add_object_without_if_callback_fails(self):
        cmd = [__file__,
               '-m', 'copy',
               '-td', 'device',
               '-tp', 'path',
               '-fs', 'ext2',
               '--no-format',
               '--format-options', 'options']  # requires --format to be true
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 2)

    def test_can_add_a_raw_object_with_all_options(self):
        cmd = [__file__,
               '--mode', 'raw',
               '--target-device', 'device',
               '--skip', '128',
               '--count', '-1',
               '--seek', '1234',
               '--chunk-size', '128',
               '--no-truncate']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_a_copy_object_with_all_options(self):
        cmd = [__file__,
               '--mode', 'copy',
               '--target-device', 'device',
               '--mount-options', 'options',
               '--target-path', 'path',
               '--filesystem', 'ext4',
               '--format',
               '--format-options', 'options']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_a_tarball_object_with_all_options(self):
        cmd = [__file__,
               '--mode', 'tarball',
               '--target-device', 'device',
               '--mount-options', 'options',
               '--target-path', 'path',
               '--filesystem', 'ext4',
               '--format',
               '--format-options', 'options']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_raw_object_with_only_required_options(self):
        cmd = [__file__,
               '--mode', 'raw',
               '--target-device', 'device']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_copy_object_with_only_required_options(self):
        cmd = [__file__,
               '--mode', 'copy',
               '--target-device', 'device',
               '--target-path', 'path',
               '--filesystem', 'ext4']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_can_add_tarball_object_with_only_required_options(self):
        cmd = [__file__,
               '--mode', 'tarball',
               '--target-device', 'device',
               '--target-path', 'path',
               '--filesystem', 'ext4']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 0)

    def test_cannot_add_raw_object_without_required_options(self):
        cmd = [__file__, '--mode', 'raw']
        result = self.runner.invoke(add_object_command, cmd)
        self.assertEqual(result.exit_code, 2)

    def test_cannot_add_copy_object_without_required_options(self):
        cmds = (
            [__file__,
             '--mode', 'copy',
             '--target-device', 'device',
             '--target-path', 'path'],
            [__file__,
             '--mode', 'copy',
             '--target-device', 'device',
             '--filesystem', 'ext4'],
            [__file__,
             '--mode', 'copy',
             '--target-path', 'path',
             '--filesystem', 'ext4']
        )
        for cmd in cmds:
            result = self.runner.invoke(add_object_command, cmd)
            self.assertEqual(result.exit_code, 2)

    def test_cannot_add_tarball_object_without_required_options(self):
        cmds = (
            [__file__,
             '--mode', 'tarball',
             '--target-device', 'device',
             '--target-path', 'path'],
            [__file__,
             '--mode', 'tarball',
             '--target-device', 'device',
             '--filesystem', 'ext4'],
            [__file__,
             '--mode', 'tarball',
             '--target-path', 'path',
             '--filesystem', 'ext4']
        )
        for cmd in cmds:
            result = self.runner.invoke(add_object_command, cmd)
            self.assertEqual(result.exit_code, 2)


class EditObjectCommandTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.runner = CliRunner()
        self.pkg_file = '.efu-test'
        self.obj_file = 'setup.py'
        self.obj_id = '1'
        self.addCleanup(self.remove_file, self.pkg_file)

        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.addCleanup(delete_environment_variable, LOCAL_CONFIG_VAR)

        data = {
            'product': '1234R',
            'objects': {
                self.obj_id: {
                    'filename': self.obj_file,
                    'target-device': '/dev/sda'
                }
            }
        }
        with open(self.pkg_file, 'w') as fp:
            json.dump(data, fp)

    def test_can_edit_object_with_edit_object_command(self):
        args = [self.obj_id, 'target-device', '/dev/sdb']
        self.runner.invoke(edit_object_command, args=args)
        with open(self.pkg_file) as fp:
            pkg = json.load(fp)
        obj = pkg['objects'][self.obj_id]
        self.assertEqual(obj['target-device'], '/dev/sdb')

    def test_edit_command_returns_0_if_successful(self):
        args = [self.obj_id, 'target-device', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 0)

    def test_edit_command_returns_1_if_package_does_not_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = '.not-exists'
        args = [self.obj_id, 'target-device', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 1)

    def test_edit_command_returns_2_if_object_does_not_exist(self):
        args = ['not-exists', 'target-device', '/dev/sdb']
        result = self.runner.invoke(edit_object_command, args=args)
        self.assertEqual(result.exit_code, 2)


class RemoveObjectCommandTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.pkg_file = '.efu-test'
        self.obj_id = '1'
        data = {
            'product': '1234R',
            'objects': {self.obj_id: {'filename': __file__}}
        }
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.addCleanup(delete_environment_variable, LOCAL_CONFIG_VAR)
        with open(self.pkg_file, 'w') as fp:
            json.dump(data, fp)
        self.addCleanup(self.remove_file, self.pkg_file)
        self.runner = CliRunner()

    def test_can_remove_image_with_remove_command(self):
        r = self.runner.invoke(remove_object_command, args=[self.obj_id])
        print(r.output)
        with open(self.pkg_file) as fp:
            package = json.load(fp)
        self.assertIsNone(package['objects'].get(self.obj_id))

    def test_remove_command_returns_0_if_successful(self):
        result = self.runner.invoke(remove_object_command, args=[self.obj_id])
        self.assertEqual(result.exit_code, 0)

    def test_remove_command_returns_1_if_package_does_not_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = '.not-exists'
        result = self.runner.invoke(remove_object_command, args=[self.obj_id])
        self.assertEqual(result.exit_code, 1)


class ShowCommandTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        self.pkg_file = '.efu-test'
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.runner = CliRunner()
        self.addCleanup(os.environ.pop, LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_file, self.pkg_file)

    def test_show_command_returns_0_if_successful(self):
        package = {
            'product': '1234',
            'objects': {
                1: {
                    'filename': __file__,
                    'mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        with open('.efu-test', 'w') as fp:
            json.dump(package, fp)
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 0)

    def test_show_command_returns_1_if_package_does_not_exist(self):
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 1)


class ExportCommandTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.pkg_file = self.create_package_file(
            self.version, [__file__], self.product)

        self.exported_pkg_file = '/tmp/efu-dump'
        self.addCleanup(self.remove_file, self.exported_pkg_file)

        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.addCleanup(delete_environment_variable, LOCAL_CONFIG_VAR)
        self.runner = CliRunner()

    def test_can_export_package_file(self):
        expected = {
            'product': self.product,
            'version': None,
            'objects': {
                '1': {
                    'filename': __file__,
                    'mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        self.assertFalse(os.path.exists(self.exported_pkg_file))
        self.runner.invoke(export_command, args=[self.exported_pkg_file])
        self.assertTrue(os.path.exists(self.exported_pkg_file))
        with open(self.exported_pkg_file) as fp:
            exported_package = json.load(fp)
        self.assertEqual(exported_package, expected)

    def test_export_package_command_returns_0_if_successful(self):
        result = self.runner.invoke(
            export_command, args=[self.exported_pkg_file])
        self.assertEqual(result.exit_code, 0)

    def test_export_command_returns_1_if_package_does_not_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = 'dont-exist'
        result = self.runner.invoke(
            export_command, args=[self.exported_pkg_file])
        self.assertFalse(os.path.exists(self.exported_pkg_file))
        self.assertEqual(result.exit_code, 1)


class NewVersionCommandTestCase(PackageMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.runner = CliRunner()
        self.pkg_file = self.create_package_file(None, [], self.product)
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file

    def test_can_set_package_version(self):
        package = Package.from_file(self.pkg_file)
        self.assertIsNone(package.version)
        result = self.runner.invoke(
            new_version_command, args=[self.version])
        package = Package.from_file(self.pkg_file)
        self.assertEqual(package.version, self.version)

    def test_new_package_version_comands_returns_0_if_successful(self):
        result = self.runner.invoke(
            new_version_command, args=[self.version])
        self.assertEqual(result.exit_code, 0)

    def test_new_package_version_comands_returns_1_without_package_file(self):
        os.environ[LOCAL_CONFIG_VAR] = 'dont-exist'
        result = self.runner.invoke(
            new_version_command, args=[self.version])
        self.assertEqual(result.exit_code, 1)


class StatusCommandTestCase(
        PackageMockMixin, HTTPServerMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.pkg_file = self.create_package_file(None, [], self.product)
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.runner = CliRunner()

    def test_status_command_returns_0_if_successful(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.package_id)
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': 'finished'}))
        result = self.runner.invoke(status_command, args=[self.package_id],
                                    catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

    def test_status_command_returns_1_if_package_doesnt_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = 'not_exists'
        result = self.runner.invoke(status_command, args=[self.package_id])
        self.assertEqual(result.exit_code, 1)

    def test_status_command_returns_2_if_status_doesnt_exist(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.package_id)
        self.httpd.register_response(path, status_code=404)
        result = self.runner.invoke(status_command, args=[self.package_id])
        self.assertEqual(result.exit_code, 2)
