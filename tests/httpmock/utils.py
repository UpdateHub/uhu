# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

from .httpd import HTTPMockServer, RequestHandler


class BaseHTTPServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.handler = RequestHandler
        cls.httpd = HTTPMockServer()
        cls.httpd.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def tearDown(self):
        self.handler.reset()

    def url(self, path='/'):
        '''Helper method that generates a URL based on HTTP mock server
        information.

        By default, it returns the server web root (eg. http://127.0.0.1:80/).

        If path is provided, it is appended into the end of the url so
        you can create any URI (eg. http://127.0.0.1:80/this/is/a/path).

        '''
        return 'http://{addr}:{port}{path}'.format(
            addr=self.httpd.server_address[0],
            port=self.httpd.server_address[1],
            path=path
        )
