# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from click.testing import CliRunner

from efu.cli.push import status_command
from efu.utils import LOCAL_CONFIG_VAR

from ..base import PushMockMixin, BaseTestCase


class StatusCommandTestCase(PushMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.runner = CliRunner()

    def test_status_command_returns_0_if_successful(self):
        self.httpd.register_response(
            '/products/{}/commits/1234/status'.format(self.product),
            status_code=200,
            body=json.dumps({'status': 'finished'})
        )
        result = self.runner.invoke(status_command, args=['1234'])
        self.assertEqual(result.exit_code, 0)

    def test_status_command_returns_1_if_package_doesnt_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = 'not_exists'
        result = self.runner.invoke(status_command, args=['1234'])
        self.assertEqual(result.exit_code, 1)

    def test_status_command_returns_2_if_commit_doesnt_exist(self):
        self.httpd.register_response(
            '/products/{}/commits/1234/status'.format(self.product),
            status_code=404,
        )
        result = self.runner.invoke(status_command, args=['1234'])
        self.assertEqual(result.exit_code, 2)
