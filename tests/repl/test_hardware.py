# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest
from unittest.mock import patch

from uhu.repl.repl import UHURepl
from uhu.repl import functions


class HardwareManagementTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = UHURepl()

    @patch('uhu.repl.functions.prompt')
    def test_can_add_a_supported_hardware_identifier(self, prompt):
        prompt.side_effect = ['PowerX']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertIn('PowerX', self.repl.package.supported_hardware)

    @patch('uhu.repl.functions.prompt')
    def test_can_remove_a_supported_hardware_identifier(self, prompt):
        functions.prompt.side_effect = ['PowerX']
        self.repl.package.supported_hardware.add('PowerX')
        self.repl.package.supported_hardware.add('PowerY')
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertNotIn('PowerX', self.repl.package.supported_hardware)
        self.assertIn('PowerY', self.repl.package.supported_hardware)

    def test_can_reset_supported_hardware_identifier_list(self):
        self.repl.package.supported_hardware.add('PowerX')
        self.repl.package.supported_hardware.add('PowerY')
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        functions.reset_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
