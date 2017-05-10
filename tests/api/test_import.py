# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest


class ImportTestCase(unittest.TestCase):

    def test_import(self):
        import uhu
        self.assertTrue(uhu)
