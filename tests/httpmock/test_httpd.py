# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import requests

from .utils import BaseHTTPServerTestCase


class HTTPServerTestCase(BaseHTTPServerTestCase):

    def test_can_register_a_response(self):
        url = self.httpd.url()
        code = 400
        body = '{"status": "manipulated"}'
        headers = {'CustomHeader': '42'}

        self.httpd.register_response(
            '/',
            status_code=code,
            headers=headers,
            body=body
        )

        response = requests.get(url)
        self.assertEqual(response.status_code, code)
        self.assertEqual(response.headers.get('CustomHeader'), '42')
        self.assertEqual(response.text, body)

    def test_can_clear_httpd_history(self):
        self.httpd.register_response('/', method='GET')
        self.httpd.register_response('/', method='POST')
        self.httpd.register_response('/', method='PUT')
        self.httpd.register_response('/', method='DELETE')
        self.httpd.register_response('/', method='HEAD')

        for _ in range(5):
            requests.get(self.httpd.url())

        self.assertEqual(len(self.httpd.responses), 1)
        self.assertEqual(len(self.httpd.responses['/']), 5)
        self.assertEqual(len(self.httpd.requests), 5)

        self.httpd.clear_history()

        self.assertEqual(len(self.httpd.responses), 0)
        self.assertEqual(len(self.httpd.requests), 0)

    def test_can_handle_http_verbs(self):
        self.httpd.register_response('/', method='GET')
        self.httpd.register_response('/', method='POST')
        self.httpd.register_response('/', method='PUT')
        self.httpd.register_response('/', method='DELETE')
        self.httpd.register_response('/', method='HEAD')

        url = self.httpd.url()

        self.assertEqual(requests.get(url).status_code, 200)
        self.assertEqual(requests.post(url).status_code, 200)
        self.assertEqual(requests.put(url).status_code, 200)
        self.assertEqual(requests.delete(url).status_code, 200)
        self.assertEqual(requests.head(url).status_code, 200)

    def test_returns_404_when_there_is_no_response_registered(self):
        response = requests.get(self.httpd.url())
        self.assertEqual(response.status_code, 404)

        response = requests.get(self.httpd.url('/not-found'))
        self.assertEqual(response.status_code, 404)

    def test_returns_405_when_there_is_no_method_registered(self):
        self.httpd.register_response('/', method='GET')
        response = requests.post(self.httpd.url())
        self.assertEqual(response.status_code, 405)

    def test_can_manipulate_status_code(self):
        code = 400
        self.httpd.register_response('/', status_code=code)
        response = requests.get(self.httpd.url())
        self.assertEqual(response.status_code, code)

        code = 405
        self.httpd.register_response('/', status_code=code)
        response = requests.get(self.httpd.url())
        self.assertEqual(response.status_code, code)

    def test_can_manipulate_body(self):
        body = '{"status": "manipulated"}'
        self.httpd.register_response('/', body=body)
        response = requests.get(self.httpd.url())
        self.assertEqual(response.text, body)

    def test_can_manipulate_headers(self):
        headers = {'CustomHeader': '42'}
        self.httpd.register_response('/', headers=headers)
        response = requests.get(self.httpd.url())
        self.assertEqual(response.headers.get('CustomHeader'), '42')

    def test_can_retrieve_request_history(self):
        self.httpd.register_response('/', method='GET')

        url = self.httpd.url()
        data = b'\0'
        headers = {'CustomHeader': '42'}

        for _ in range(3):
            requests.post(url, data=data, headers=headers)
        self.assertEqual(len(self.httpd.requests), 3)

        request = self.httpd.requests[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'\0')
        self.assertEqual(request.headers['CustomHeader'], '42')
