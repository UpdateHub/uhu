# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import subprocess
import unittest


class CLITestCase(unittest.TestCase):

    def test_efu_is_a_cli_command(self):
        response = subprocess.call('efu')
        self.assertEqual(response, 0)

    def test_efu_can_be_called_as_a_module(self):
        response = subprocess.call(['python', '-m', 'efu'])
        self.assertEqual(response, 0)
