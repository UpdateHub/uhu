# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from click.testing import CliRunner

from efu.cli.package import pull_command

from ..utils import BasePullTestCase


class PullCommandTestCase(BasePullTestCase):

    def setUp(self):
        super().setUp()
        self.package.dump(self.pkg_fn)
        self.runner = CliRunner()

    def test_pull_command_full_returns_0_if_successful(self):
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--full'])
        print(result.output)
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_metadata_returns_0_if_successful(self):
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--metadata'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_full_returns_0_if_file_exists(self):
        with open(self.obj_fn, 'wb') as fp:
            fp.write(self.obj_content)
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--full'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_returns_1_if_package_does_not_exist(self):
        os.remove(self.pkg_fn)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 1)

    def test_pull_command_returns_2_if_product_not_set(self):
        with open(self.pkg_fn, 'w') as fp:
            json.dump({}, fp)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 2)

    def test_pull_command_returns_3_if_package_has_objects(self):
        self.package.objects.add_list()
        self.package.objects.add(
            0, __file__, mode='raw', options={'target-device': '/dev/sda'})
        self.package.dump(self.pkg_fn)
        result = self.runner.invoke(pull_command, args=[self.pkg_uid])
        self.assertEqual(result.exit_code, 3)

    def test_pull_command_returns_4_if_package_id_does_not_exist(self):
        result = self.runner.invoke(pull_command, args=['not-exist'])
        self.assertEqual(result.exit_code, 4)

    def test_pull_command_returns_5_if_file_exists_and_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('different')
        result = self.runner.invoke(
            pull_command, args=[self.pkg_uid, '--full'])
        self.assertEqual(result.exit_code, 5)
