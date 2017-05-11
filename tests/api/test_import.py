# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest


class ImportTestCase(unittest.TestCase):

    def test_import(self):
        import uhu
        self.assertTrue(uhu)
