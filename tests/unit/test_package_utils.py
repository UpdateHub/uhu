# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest

from efu.package.exceptions import DotEfuExistsError
from efu.package.utils import create_efu_file


class UtilsTestCase(unittest.TestCase):

    def remove_efu_file_cleanup(self):
        try:
            os.remove('.efu')
        except:
            # file already deleted
            pass

    def setUp(self):
        self.addCleanup(self.remove_efu_file_cleanup)

    def test_can_create_efu_file(self):
        create_efu_file(product='1234X', version='2.0')
        self.assertTrue(os.path.exists('.efu'))
        with open('.efu') as fp:
            data = json.load(fp)
        self.assertEqual(data['product'], '1234X')
        self.assertEqual(data['version'], '2.0')

    def test_do_not_create_efu_file_if_it_exists(self):
        with open('.efu', 'w'):
            pass
        with self.assertRaises(DotEfuExistsError):
            create_efu_file(product='1234X', version='2.0')
