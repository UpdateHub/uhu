# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, Mock

import requests

from uhu import utils
from uhu.updatehub._request import Request
from uhu.updatehub.http import (
    format_server_error, HTTPError, request, UNKNOWN_ERROR, get, post, put)
from uhu.updatehub.auth import UHV1Signature


def set_credentials():
    os.environ[utils.ACCESS_ID_VAR] = 'access'
    os.environ[utils.ACCESS_SECRET_VAR] = 'secret'


class RequestTestCase(unittest.TestCase):

    def setUp(self):
        set_credentials()

    @patch('uhu.updatehub.http.request')
    def test_can_make_GET_POST_and_PUT_requests(self, mock):
        url = 'localhost'
        get(url)
        mock.assert_called_with('GET', url)
        post(url)
        mock.assert_called_with('POST', url)
        put(url)
        mock.assert_called_with('PUT', url)

    def test_request_date_is_in_utc(self):
        expected = datetime.now(timezone.utc).timestamp()
        observed = Request('', 'POST').date.timestamp()
        # 60 seconds of tolerance between expected and observed
        self.assertAlmostEqual(observed, expected, delta=60)

    @patch('uhu.updatehub._request.datetime')
    @patch('uhu.updatehub._request.get_version', return_value='2.0')
    def test_request_has_minimal_headers(self, mock_version, mock_date):
        mock_date.now.return_value = datetime(1970, 1, 1, tzinfo=timezone.utc)
        request = Request('https://localhost/', 'POST', b'\0')
        self.assertEqual(len(request.headers), 6)
        self.assertEqual(request.headers.get('Host'), 'localhost')
        self.assertEqual(request.headers.get('Timestamp'), 0)
        self.assertEqual(
            request.headers.get('Api-Content-Type'),
            'application/vnd.updatehub-v1+json')
        self.assertEqual(
            request.headers.get('Content-sha256'),
            '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d')
        self.assertEqual(
            request.headers.get('User-Agent'), 'updatehub-utils/2.0')

    def test_request_does_not_send_json_content_type_by_default(self):
        request = Request('https://localhost/', 'POST')
        self.assertIsNone(request.headers.get('Content-Type'))

    def test_can_set_json_content_type(self):
        request = Request('https://localhost/', 'POST', b'{}', json=True)
        header = request.headers.get('Content-Type')
        self.assertIsNotNone(header)
        self.assertEqual(header, 'application/json')

    def test_header_content_sha256_when_bytes(self):
        payload = b'bytes'
        request = Request('localhost', 'POST', payload)
        expected = hashlib.sha256(payload).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_header_content_sha256_when_string(self):
        payload = 'string'
        request = Request('localhost', 'POST', payload)
        expected = hashlib.sha256(payload.encode()).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_prepared_headers_are_strings(self):
        request = Request('localhost', 'POST')
        headers = request.headers
        prepared_headers = request._prepare_headers()

        self.assertEqual(prepared_headers.keys(), headers.keys())

        for value in prepared_headers.values():
            self.assertIs(type(value), str)

        for header in headers:
            self.assertEqual(str(headers[header]), prepared_headers[header])

    @patch('uhu.updatehub._request.requests.request')
    def test_send_request(self, request):
        Request('localhost', 'GET').send()
        args, kwargs = request.call_args
        self.assertEqual(args, ('GET', 'localhost'))
        self.assertEqual(kwargs.get('timeout'), 30)

    @patch('uhu.updatehub._request.requests.request')
    def test_request_is_signed(self, request):
        Request('/signed', 'GET').send()
        headers = request.call_args[1]['headers']
        self.assertIsNotNone(headers.get('Authorization'))

    def test_host_header_includes_port_if_provided(self):
        req = Request('http://localhost:123', 'GET')
        expected = 'localhost:123'
        observed = req.headers.get('Host')
        self.assertEqual(observed, expected)

    def test_host_header_does_not_include_port_if_not_provided(self):
        req = Request('http://localhost', 'GET')
        expected = 'localhost'
        observed = req.headers.get('Host')
        self.assertEqual(observed, expected)

    @patch('uhu.updatehub._request.requests.request')
    def test_can_pass_extra_kwargs_to_requests(self, mock):
        Request('http://localhost', 'GET', stream=True).send()
        observed = list(mock.call_args)[1].get('stream')
        self.assertTrue(observed)


class CanonicalRequestTestCase(unittest.TestCase):

    @patch('uhu.updatehub._request.datetime')
    @patch('uhu.updatehub._request.get_version', return_value='2.0')
    def test_canonical_request(self, mock_version, mock_date):
        mock_date.now.return_value = datetime(1970, 1, 1, tzinfo=timezone.utc)
        request = Request(
            'http://localhost/upload?c=3&b=2&a=1',
            'POST',
            b'\0',
        )
        expected = '''POST
/upload
a=1&b=2&c=3
accept:application/json
api-content-type:application/vnd.updatehub-v1+json
content-sha256:6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d
host:localhost
timestamp:0.0
user-agent:updatehub-utils/2.0

6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'''
        self.assertEqual(request.canonical(), expected)

    def test_canonical_query(self):
        url = 'https://localhost/?c=000&bb=111&aaa=222'
        request = Request(url, 'POST')
        expected = 'aaa=222&bb=111&c=000'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_is_correctly_escaped(self):
        url = 'https://localhost/?to-be-scaped=scape me!&b=1&a=2'
        request = Request(url, 'POST')
        expected = 'a=2&b=1&to-be-scaped=scape%20me%21'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_handles_repeated_values(self):
        url = 'https://localhost/?b=3&a=3&b=2&a=2&b=1&a=1'
        request = Request(url, 'POST')
        expected = 'a=1&a=2&a=3&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_can_sort_escaped_repeated_values(self):
        url = 'https://localhost/?b=3&a=1&b=2&a=!&b=1&a= '
        request = Request(url, 'POST')
        expected = 'a=%20&a=%21&a=1&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_headers(self):
        request = Request('http://foo.bar.com.br', 'POST')
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


class SignedRequestTestCase(unittest.TestCase):

    def setUp(self):
        set_credentials()

    def test_signed_request_has_the_authorization_header(self):
        request = Request('https://127.0.0.1/upload', 'POST')
        header = request.headers.get('Authorization', None)
        self.assertIsNone(header)

        request._sign()
        header = request.headers.get('Authorization', None)
        self.assertIsNotNone(header)

    @patch('uhu.updatehub._request.requests.request')
    def test_signatured_is_calculated_with_right_headers(self, mock):
        request = Request('localhost', 'POST')
        self.assertIsNone(request.headers.get('Authorization', None))

        sig = UHV1Signature(request, 'access', 'secret').signature
        self.assertIsNone(request.headers.get('Authorization', None))

        # It is right when we sign the request
        request._sign()
        self.assertIsNotNone(request.headers.get('Authorization', None))
        self.assertEqual(sig, request.headers['Authorization'])

        del request.headers['Authorization']
        request.send()

        args, kwargs = mock.call_args
        self.assertEqual(kwargs['headers']['Authorization'], sig)

        # It is right when we send the request
        request = Request('localhost', 'POST')
        self.assertIsNone(request.headers.get('Authorization', None))

        sig = UHV1Signature(request, 'access', 'secret').signature
        self.assertIsNone(request.headers.get('Authorization', None))
        request.send()

        args, kwargs = mock.call_args
        self.assertEqual(kwargs['headers']['Authorization'], sig)


class FormatServerErrorTestCase(unittest.TestCase):

    def setUp(self):
        self.response = Mock()

    def test_returns_unkown_error_when_unknown_error(self):
        self.response.json.return_value = {}
        observed = format_server_error(self.response)
        self.assertEqual(observed, UNKNOWN_ERROR)

    def test_returns_unkown_error_when_cant_decode_error(self):
        self.response.json.side_effect = ValueError
        observed = format_server_error(self.response)
        self.assertEqual(observed, UNKNOWN_ERROR)

    def test_returns_error_message_when_error_message(self):
        self.response.json.return_value = {'error_message': 'message'}
        observed = format_server_error(self.response)
        self.assertEqual(observed, 'message')

    def test_returns_error_list_when_error_list(self):
        self.response.json.return_value = {
            'errors': {
                'field': ['message'],
            },
        }
        observed = format_server_error(self.response)
        self.assertEqual(observed, '- field: message')

    def test_returns_unknown_error_when_list_is_invalid(self):
        invalid_errors = [
            {'errors': 1},
            {'errors': {'field': None}},
        ]
        for errors in invalid_errors:
            self.response.json.return_value = errors
            observed = format_server_error(self.response)
            self.assertEqual(observed, UNKNOWN_ERROR)


class RequestErrorsTestCase(unittest.TestCase):

    def setUp(self):
        set_credentials()

    @patch('uhu.updatehub.http.requests.request')
    def test_returns_response_if_no_error_is_present(self, mock):
        mock.return_value.ok = True
        mock.return_value.status_code = 200
        response = request('GET', 'foo', sign=False)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.ok)

    @patch('uhu.updatehub.http.requests.request')
    def test_raises_error_when_invalid_url(self, mock):
        exceptions = [
            requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
            requests.exceptions.URLRequired,
            requests.exceptions.InvalidURL,
        ]
        mock.side_effect = exceptions
        for _ in exceptions:
            with self.assertRaises(HTTPError):
                request('GET', 'foo')

    @patch('uhu.updatehub.http.requests.request')
    def test_raises_error_when_server_is_unavailable(self, mock):
        exceptions = [requests.ConnectionError, requests.ConnectTimeout]
        mock.side_effect = exceptions
        for _ in exceptions:
            with self.assertRaises(HTTPError):
                request('GET', 'foo')

    @patch('uhu.updatehub.http.requests.request')
    def test_raises_error_with_any_other_requests_exception(self, mock):
        exceptions = [
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError,
            requests.exceptions.SSLError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.URLRequired,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
            requests.exceptions.InvalidURL,
            requests.exceptions.InvalidHeader,
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ContentDecodingError,
            requests.exceptions.StreamConsumedError,
            requests.exceptions.RetryError,
            requests.exceptions.UnrewindableBodyError,
        ]
        mock.side_effect = exceptions
        for _ in exceptions:
            with self.assertRaises(HTTPError):
                request('GET', 'foo')

    @patch('uhu.updatehub.http.requests.request')
    def test_raises_error_when_unathorized(self, mock):
        mock.return_value.status_code = 401
        with self.assertRaises(HTTPError):
            request('GET', 'foo')

    @patch('uhu.updatehub.http.requests.request')
    def test_raises_error_if_response_is_not_ok(self, mock):
        mock.return_value.ok = False
        with self.assertRaises(HTTPError):
            request('GET', 'foo')

    def test_raises_error_if_missing_credentials(self):
        del os.environ[utils.ACCESS_ID_VAR]
        del os.environ[utils.ACCESS_SECRET_VAR]
        with self.assertRaises(HTTPError):
            request('GET', 'foo')
