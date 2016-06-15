# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

from .httpd import HTTPMockServer


class BaseHTTPServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPMockServer()
        cls.httpd.start()
        cls.SERVER_ADDRESS, cls.SERVER_PORT = cls.httpd.server_address

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        self.url = 'http://{address}:{port}'.format(
            address=self.SERVER_ADDRESS,
            port=self.SERVER_PORT,
        )
