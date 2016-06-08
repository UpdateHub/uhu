# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import unittest

from efu.auth import SignatureV1
from efu.request import Request


class RequestTestCase(unittest.TestCase):

    def test_canonical_request(self):
        request = Request(
            'http://localhost/upload?c=3&b=2&a=1',
            'post',
            b'\0',
        )
        expected = '''POST
/upload
a=1&b=2&c=3
host:localhost

6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'''
        self.assertEqual(request.canonical(), expected)

    def test_canonical_payload_when_bytes(self):
        payload = b'bytes'
        request = Request('localhost', 'post', payload)
        expected = hashlib.sha256(payload).hexdigest()
        observed = request._canonical_payload()
        self.assertEqual(observed, expected)

    def test_canonical_payload_when_string(self):
        payload = 'string'
        request = Request('localhost', 'post', payload)
        expected = hashlib.sha256(payload.encode()).hexdigest()
        observed = request._canonical_payload()
        self.assertEqual(observed, expected)

    def test_canonical_query(self):
        url = 'https://localhost/?c=000&bb=111&aaa=222'
        request = Request(url, 'post', '')
        expected = 'aaa=222&bb=111&c=000'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_is_correctly_escaped(self):
        url = 'https://localhost/?to-be-scaped=scape me!&b=1&a=2'
        request = Request(url, 'post', '')
        expected = 'a=2&b=1&to-be-scaped=scape%20me%21'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_handles_repeated_values(self):
        url = 'https://localhost/?b=3&a=3&b=2&a=2&b=1&a=1'
        request = Request(url, 'post', '')
        expected = 'a=1&a=2&a=3&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_can_sort_escaped_repeated_values(self):
        url = 'https://localhost/?b=3&a=1&b=2&a=!&b=1&a= '
        request = Request(url, 'post', '')
        expected = 'a=%20&a=%21&a=1&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_headers(self):
        request = Request('http://foo.bar.com.br', 'post', '')
        request.headers = {
            'Host': 'foo.bar.com.br',
            'x-efu-content-sha256': '1234',
            'x-efu-date': ' 1 ',
            'Date': 'Tue, 15 Nov 1994 08:12:31 GMT',
            'Accept': 'text/json',
        }
        expected = '''accept:text/json
date:Tue, 15 Nov 1994 08:12:31 GMT
host:foo.bar.com.br
x-efu-content-sha256:1234
x-efu-date:1'''
        observed = request._canonical_headers()
        self.assertEqual(observed, expected)


class SignedRequestTestCase(unittest.TestCase):

    def test_signed_request_has_the_authorization_header(self):
        request = Request('https://127.0.0.1/upload', 'post', '')
        signed_request = SignatureV1(request, 'ACCESS_ID', 'SECRET').sign()
        header = signed_request.headers.get('Authorization', None)
        self.assertIsNotNone(header)
