# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest


class ImportTestCase(unittest.TestCase):

    def test_import(self):
        import efu
        self.assertTrue(efu)
