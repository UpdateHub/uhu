# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from click.testing import CliRunner

from efu.utils import LOCAL_CONFIG_VAR
from efu.cli.config import cleanup_command


class CleanupCommandTestCase(unittest.TestCase):

    def setUp(self):
        os.environ[LOCAL_CONFIG_VAR] = '.efu-test'
        self.runner = CliRunner()
        self.addCleanup(os.environ.pop, LOCAL_CONFIG_VAR)

    def test_can_cleanup_efu_files(self):
        open('.efu-test', 'w').close()
        self.assertTrue(os.path.exists('.efu-test'))
        self.runner.invoke(cleanup_command)
        self.assertFalse(os.path.exists('.efu-test'))

    def test_cleanup_command_returns_0_if_successful(self):
        open('.efu-test', 'w').close()
        result = self.runner.invoke(cleanup_command)
        self.assertEqual(result.exit_code, 0)

    def test_cleanup_command_returns_1_if_package_is_already_deleted(self):
        result = self.runner.invoke(cleanup_command)
        self.assertEqual(result.exit_code, 1)
