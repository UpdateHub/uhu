# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu.core import Product
from efu.utils import LOCAL_CONFIG_VAR

from ..base import delete_environment_variable, ObjectMockMixin


class ProductTestCase(ObjectMockMixin, unittest.TestCase):

    def setUp(self):
        self.local_config_fn = self.create_file(b'')
        os.environ[LOCAL_CONFIG_VAR] = self.local_config_fn
        self.addCleanup(delete_environment_variable, LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_file, self.local_config_fn)

    def test_can_load_a_product(self):
        with open(self.local_config_fn, 'w') as fp:
            fp.write('{"product": 42}')
        expected = 42
        product = Product()
        self.assertEqual(product.uid, expected)

    def test_can_set_a_product(self):
        config_fn = '/tmp/.efu'
        os.environ[LOCAL_CONFIG_VAR] = config_fn
        self.addCleanup(self.remove_file, config_fn)

        expected = 42
        product = Product.use(expected)
        self.assertEqual(product.uid, expected)

    def test_cannot_load_product_when_config_doesnt_exist(self):
        os.environ[LOCAL_CONFIG_VAR] = 'not-exists'
        with self.assertRaises(FileNotFoundError):
            Product()

    def test_cannot_overwrite_an_already_set_product(self):
        with open(self.local_config_fn, 'w') as fp:
            fp.write('{"product": 42}')
        with self.assertRaises(FileExistsError):
            Product.use(101)

    def test_can_overwrite_a_product_if_force(self):
        with open(self.local_config_fn, 'w') as fp:
            fp.write('{"product": 42}')
        product = Product.use(101, force=True)
        self.assertEqual(product.uid, 101)
