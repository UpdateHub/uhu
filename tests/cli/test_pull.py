# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from click.testing import CliRunner

from efu.cli.package import pull_command
from efu.core.installation_set import InstallationSetMode
from efu.core.package import Package
from efu.utils import SERVER_URL_VAR

from utils import BasePullTestCase


class PullCommandTestCase(BasePullTestCase):

    def setUp(self):
        super().setUp()
        self.package.dump(self.pkg_fn)
        self.runner = CliRunner()

    def test_pull_command_with_objects_returns_0_if_successful(self):
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_with_objects_returns_0_if_file_exists(self):
        with open(self.obj_fn, 'wb') as fp:
            fp.write(self.obj_content)
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_with_metadata_returns_0_if_successful(self):
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--metadata'])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists('metadata.json'))

    def test_pull_command_returns_1_if_package_does_not_exist(self):
        os.remove(self.pkg_fn)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 1)

    def test_pull_command_returns_2_if_product_not_set(self):
        Package(InstallationSetMode.Single).dump(self.pkg_fn)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 2)

    def test_pull_command_returns_3_if_package_has_objects(self):
        self.package.objects.create(
            __file__, 'raw', {'target-device': '/dev/sda'})
        self.package.dump(self.pkg_fn)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 3)

    def test_pull_command_returns_4_if_cant_reach_server(self):
        self.set_env_var(SERVER_URL_VAR, 'http://easyfota-unreach.com')
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 4)

    def test_pull_command_returns_5_if_package_id_does_not_exist(self):
        result = self.runner.invoke(pull_command, args=['not-exist'])
        self.assertEqual(result.exit_code, 5)

    def test_pull_command_returns_6_if_file_exists_and_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('different')
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 6)

    def test_pull_command_returns_7_if_cant_download_object(self):
        # url to download object
        path = '/products/{}/packages/{}/objects/{}'.format(
            self.product, self.pkg_uid, self.obj_sha256)
        self.httpd.register_response(path, 'GET', status_code=404)
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--objects'])
        self.assertEqual(result.exit_code, 7)

    def test_can_pull_to_an_inexistent_output(self):
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--output', '/tmp/yey'])
        self.assertEqual(result.exit_code, 0)
