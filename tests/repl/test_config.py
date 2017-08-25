# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest
from unittest.mock import patch

from uhu.config import config, AUTH_SECTION
from uhu.repl import functions


class PackageTestCase(unittest.TestCase):

    @patch('uhu.repl.functions.prompt')
    @patch('uhu.repl.functions.config.set_credentials')
    def test_can_set_authentication_credentials(self, set_initial, prompt):
        prompt.side_effect = ['access', 'secret']
        functions.set_authentication()
        set_initial.assert_called_with('access', 'secret')
