# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import requests

from efu.auth import SignatureV1
from efu.request import Request

from ..base import ConfigTestCaseMixin
from ..httpmock.utils import BaseHTTPServerTestCase


class RequestTestCase(BaseHTTPServerTestCase):

    def test_request_date_is_in_utc(self):
        expected = datetime.now(timezone.utc).timestamp()
        observed = Request('', 'post', '').date.timestamp()
        # 1 second of tolerance between expected and observed
        self.assertAlmostEqual(observed, expected, delta=60)

    @patch('efu.request.datetime')
    def test_request_has_minimal_headers(self, mock):
        mock_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        mock.now.return_value = mock_date

        request = Request('https://localhost/', 'post', b'\0')

        host = request.headers.get('Host')
        timestamp = request.headers.get('Timestamp')
        sha256 = request.headers.get('Content-sha256')
        api = request.headers.get('Api-Content-Type')

        self.assertEqual(len(request.headers), 4)
        self.assertEqual(host, 'localhost')
        self.assertEqual(timestamp, 0)
        self.assertEqual(api, 'application/vnd.fota-server-v1+json')
        self.assertEqual(
            sha256,
            '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'
        )

    def test_header_content_sha256_when_bytes(self):
        payload = b'bytes'
        request = Request('localhost', 'post', payload)
        expected = hashlib.sha256(payload).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_header_content_sha256_when_string(self):
        payload = 'string'
        request = Request('localhost', 'post', payload)
        expected = hashlib.sha256(payload.encode()).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_prepared_headers_are_strings(self):
        request = Request('localhost', 'post', '')
        headers = request.headers
        prepared_headers = request._prepare_headers()

        self.assertEqual(prepared_headers.keys(), headers.keys())

        for value in prepared_headers.values():
            self.assertIs(type(value), str)

        for header in headers:
            self.assertEqual(str(headers[header]), prepared_headers[header])

    def test_send_request(self):
        self.httpd.register_response('/', body='{"status": "ok"}')
        request = Request(self.httpd.url(), 'GET', '')
        response = request.send()
        self.assertEqual(response.json()['status'], 'ok')

    def test_request_is_signed(self):
        self.httpd.register_response('/signed', body='{"status": "ok"}')
        Request(self.httpd.url('/signed'), 'GET', '').send()
        response = self.httpd.requests[-1]
        auth_header = response.headers.get('Authorization')
        self.assertIsNotNone(auth_header)


class CanonicalRequestTestCase(unittest.TestCase):

    @patch('efu.request.datetime')
    def test_canonical_request(self, mock):
        date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        mock.now.return_value = date
        request = Request(
            'http://localhost/upload?c=3&b=2&a=1',
            'post',
            b'\0',
        )
        expected = '''POST
/upload
a=1&b=2&c=3
api-content-type:application/vnd.fota-server-v1+json
content-sha256:6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d
host:localhost
timestamp:0.0

6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'''
        self.assertEqual(request.canonical(), expected)

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
            'Content-sha256': '1234',
            'Timestamp': 123456.1234,
            'Accept': 'text/json',
        }
        expected = '''accept:text/json
content-sha256:1234
host:foo.bar.com.br
timestamp:123456.1234'''
        observed = request._canonical_headers()
        self.assertEqual(observed, expected)


class SignedRequestTestCase(ConfigTestCaseMixin, BaseHTTPServerTestCase):

    def test_signed_request_has_the_authorization_header(self):
        request = Request('https://127.0.0.1/upload', 'post', '')
        header = request.headers.get('Authorization', None)
        self.assertIsNone(header)

        request._sign()
        header = request.headers.get('Authorization', None)
        self.assertIsNotNone(header)
