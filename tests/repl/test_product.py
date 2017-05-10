# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import tempfile
import unittest

from efu.core.manager import InstallationSetMode
from efu.core.package import Package
from efu.repl.repl import EFURepl
from efu.repl import functions


class ProductTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = EFURepl()

    def test_can_set_product_uid(self):
        self.assertIsNone(self.repl.package.product)
        self.repl.arg = '123456789'
        functions.set_product_uid(self.repl)
        self.assertEqual(self.repl.package.product, '123456789')

    def test_set_product_updates_prompt(self):
        self.assertEqual(self.repl.prompt, 'efu> ')
        self.repl.arg = '123456789'
        functions.set_product_uid(self.repl)
        # only the first 6 chars must appears
        self.assertEqual(self.repl.prompt, '[123456] efu> ')

    def test_start_prompt_with_package_updates_prompt(self):
        _, fn = tempfile.mkstemp()
        self.addCleanup(os.remove, fn)
        pkg = Package(InstallationSetMode.Single, product='123456789')
        pkg.dump(fn)
        self.repl = EFURepl(fn)
        self.assertEqual(self.repl.prompt, '[123456] efu> ')

    def test_set_product_raises_error_if_missing_product(self):
        with self.assertRaises(ValueError):
            functions.set_product_uid(self.repl)
