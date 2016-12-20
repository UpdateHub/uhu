# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import shutil
import tempfile

from click.testing import CliRunner

from efu.cli.package import pull_command
from efu.core.manager import InstallationSetMode
from efu.utils import SERVER_URL_VAR

from utils import BasePullTestCase


class PullCommandTestCase(BasePullTestCase):

    def setUp(self):
        super().setUp()
        self.runner = CliRunner()

    def test_pull_command_returns_0_if_successful(self):
        self.assertFalse(os.path.exists(self.pkg_fn))
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertTrue(os.path.exists(self.pkg_fn))
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_with_objects_returns_0_if_successful(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertTrue(os.path.exists(self.obj_fn))
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_with_objects_returns_0_if_file_exists(self):
        with open(self.obj_fn, 'wb') as fp:
            fp.write(self.obj_content)
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_with_metadata_returns_0_if_successful(self):
        self.assertFalse(os.path.exists('metadata.json'))
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--metadata'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists('metadata.json'))

    def test_pull_command_returns_1_if_dot_efu_exists(self):
        self.package.dump(self.pkg_fn)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 1)

    def test_pull_command_returns_2_if_cant_reach_server(self):
        self.set_env_var(SERVER_URL_VAR, 'http://easyfota-unreach.com')
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 2)

    def test_pull_command_returns_2_if_package_id_does_not_exist(self):
        result = self.runner.invoke(pull_command, args=['not-exist'])
        self.assertEqual(result.exit_code, 2)

    def test_pull_command_returns_2_if_file_exists_and_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('different')
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 2)

    def test_pull_command_returns_2_if_cant_download_object(self):
        path = '/products/{}/packages/{}/objects/{}'.format(
            self.product, self.pkg_uid, self.obj_sha256)
        self.httpd.register_response(path, 'GET', status_code=404)
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 2)

    def test_can_pull_to_an_inexistent_directory(self):
        output = tempfile.mkdtemp()
        os.rmdir(output)
        self.addCleanup(shutil.rmtree, output)

        self.assertFalse(os.path.exists(output))
        result = self.runner.invoke(pull_command, args=[
            self.pkg_uid, '--metadata', '--objects', '--output', output])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(output))
        self.assertTrue(os.path.exists(os.path.join(output, 'metadata.json')))
        self.assertTrue(os.path.exists(os.path.join(output, self.obj_fn)))
        self.assertTrue(os.path.exists(os.path.join(output, self.pkg_fn)))
