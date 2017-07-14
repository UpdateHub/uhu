# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest
from unittest.mock import Mock, patch

from click.testing import CliRunner

from uhu.cli.package import push_command
from uhu.core.updatehub import UpdateHubError
from uhu.http import HTTPError


class PushCommandTestCase(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch('uhu.cli.package.open_package')
    def test_returns_0_when_success(self, open_package):
        open_package.return_value.__enter__.return_value = Mock()
        result = self.runner.invoke(push_command)
        self.assertEqual(result.exit_code, 0)

    @patch('uhu.cli.package.open_package')
    def test_returns_2_when_updatehub_error(self, open_package):
        package = Mock()
        package.push.side_effect = UpdateHubError
        open_package.return_value.__enter__.return_value = package
        result = self.runner.invoke(push_command)
        self.assertEqual(result.exit_code, 2)

    @patch('uhu.cli.utils.show_cursor')
    def test_always_display_cursor_after_all(self, show_cursor):
        effects = [None, UpdateHubError, Exception]
        package = Mock()
        package.push.side_effect = effects
        for effect in effects:
            result = self.runner.invoke(push_command)
        self.assertEqual(show_cursor.call_count, len(effects))
