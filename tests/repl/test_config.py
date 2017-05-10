# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest
from unittest.mock import patch

from uhu.config import config, Sections
from uhu.repl import functions


class PackageTestCase(unittest.TestCase):

    @patch('uhu.repl.functions.prompt')
    def test_can_set_authentication_credentials(self, prompt):
        prompt.side_effect = ['access', 'secret']
        functions.set_authentication()
        self.assertEqual(
            config.get('access_id', section=Sections.AUTH), 'access')
        self.assertEqual(
            config.get('access_secret', section=Sections.AUTH), 'secret')
