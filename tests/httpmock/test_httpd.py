# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import requests

from .utils import BaseHTTPServerTestCase
from .httpd import RequestHandler as handler


class HTTPServerTestCase(BaseHTTPServerTestCase):

    def test_restores_to_original_state_after_request(self):
        code = 400
        headers = {'X-manipulated': 'manipulated'}
        body = {'status': 'manipulated'}

        handler.code = code
        handler.response_headers = headers
        handler.body = body

        response = requests.get(self.url)
        self.assertEqual(response.status_code, code)
        self.assertEqual(response.json(), body)
        self.assertEqual(response.headers.get('X-manipulated'), 'manipulated')

        response = requests.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get('X-manipulated'))
        self.assertEqual(response.text, '')

    def test_can_manipulate_status_code(self):
        code = 400
        handler.code = code
        response = requests.get(self.url)
        self.assertEqual(response.status_code, code)

        code = 405
        handler.code = code
        response = requests.get(self.url)
        self.assertEqual(response.status_code, code)

    def test_can_manipulate_body(self):
        body = {'status': 'manipulated'}
        handler.body = body
        response = requests.get(self.url)
        self.assertEqual(response.json(), body)

    def test_can_manipulate_headers(self):
        handler.response_headers = {'X-manipulated': 'manipulated'}
        response = requests.get(self.url)
        self.assertEqual(response.headers.get('X-manipulated'), 'manipulated')

    def test_can_handle_http_verbs(self):
        response = requests.get(self.url)
        self.assertEqual(response.status_code, 200)

        response = requests.post(self.url)
        self.assertEqual(response.status_code, 200)

        response = requests.put(self.url)
        self.assertEqual(response.status_code, 200)

        response = requests.delete(self.url)
        self.assertEqual(response.status_code, 200)

        response = requests.head(self.url)
        self.assertEqual(response.status_code, 200)
