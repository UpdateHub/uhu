# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import threading
import unittest
from http.server import HTTPServer

from httpd import GenericHTTPRequestHandler as handler


class BaseHTTPServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(
            ('127.0.0.1', 0),
            handler,
        )
        cls.SERVER_ADDRESS, cls.SERVER_PORT = cls.httpd.server_address
        threading.Thread(target=cls.httpd.serve_forever).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        self.url = 'http://{address}:{port}'.format(
            address=self.SERVER_ADDRESS,
            port=self.SERVER_PORT,
        )
