# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os

from click.testing import CliRunner

from efu.package.exceptions import PackageFileDoesNotExistError
from efu.pull.parser import pull_command
from efu.push.exceptions import CommitDoesNotExist

from ..base import EFUTestCase, PullMockMixin


class PullCommandTestCase(PullMockMixin, EFUTestCase):

    def setUp(self):
        super().setUp()
        self.set_directories()
        self.set_package_var()
        self.set_file_image()
        self.set_commit()

        with open(self.package_fn, 'w') as fp:
            json.dump({'product': self.product_id}, fp)

        self.metadata = {
            'product': self.product_id,
            'version': self.version,
            'images': [
                {
                    'filename': self.image_fn,
                    'install-mode': 'raw',
                    'size': 4,
                    'sha256sum': self.image_sha256sum
                }
            ]
        }
        self.set_urls()
        self.runner = CliRunner()

    def test_pull_command_full_returns_0_if_successful(self):
        result = self.runner.invoke(pull_command, args=[self.commit, '--full'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_metadata_returns_0_if_successful(self):
        result = self.runner.invoke(
            pull_command, args=[self.commit, '--metadata'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_full_returns_0_if_file_exists(self):
        with open(self.image_fn, 'wb') as fp:
            fp.write(self.image_content)
        result = self.runner.invoke(pull_command, args=[self.commit, '--full'])
        self.assertEqual(result.exit_code, 0)

    def test_pull_command_returns_1_if_package_does_not_exist(self):
        os.remove(self.package_fn)
        result = self.runner.invoke(pull_command, args=[self.commit])
        self.assertEqual(result.exit_code, 1)

    def test_pull_command_returns_2_if_commit_does_not_exist(self):
        result = self.runner.invoke(pull_command, args=['not-exist'])
        self.assertEqual(result.exit_code, 2)

    def test_pull_command_returns_3_if_package_exists(self):
        with open(self.package_fn, 'w') as fp:
            json.dump({'product': self.product_id, 'version': '2.0'}, fp)
        result = self.runner.invoke(pull_command, args=[self.commit])
        self.assertEqual(result.exit_code, 3)

    def test_pull_command_returns_4_if_file_exists_and_diverges(self):
        with open(self.image_fn, 'w') as fp:
            fp.write('different')
        result = self.runner.invoke(pull_command, args=[self.commit, '--full'])
        self.assertEqual(result.exit_code, 4)
