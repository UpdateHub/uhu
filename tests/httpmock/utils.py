# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

from .httpd import HTTPMockServer


class BaseHTTPServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPMockServer()
        cls.httpd.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def tearDown(self):
        self.httpd.clear_history()
