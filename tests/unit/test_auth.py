# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest
from unittest.mock import Mock

from efu.auth import SignatureV1


class SignatureV1TestCase(unittest.TestCase):

    def setUp(self):
        self.request = Mock()
        self.request.headers = {
            'foo': 'bar',
            'Host': 'localhost',
            'x-efu-timestamp': '1',
            'bar': 'foo',
        }
        self.request.canonical.return_value = '000'
        self.request.timestamp = 1

    def test_signed_headers(self):
        expected = 'bar;foo;host;x-efu-timestamp'
        signature = SignatureV1(self.request, '', '')
        observed = signature._signed_headers()
        self.assertEqual(observed, expected)

    def test_message(self):
        expected = '''EFU-V1
1
000'''
        signature = SignatureV1(self.request, '', '')
        observed = signature._message()
        self.assertEqual(observed, expected)

    def test_key(self):
        expected = '1a0b1127ff608b026c90bdc5c44200d8bf5287278e8d48d5983949869c26cb4f'  # nopep8
        signature = SignatureV1(self.request, '', 'SECRET')
        observed = signature._key()
        self.assertEqual(observed, expected)

    def test_signature(self):
        expected = '59d88fae7559e8b1132341f16164a39a4e9e26e2885213151fe6490b35e670a0'  # nopep8
        signature = SignatureV1(self.request, '', 'SECRET')
        observed = signature._signature()
        self.assertEqual(observed, expected)

    def test_header_value(self):
        expected = 'EFU-V1 Credential=123ACCESSID, SignedHeaders=bar;foo;host;x-efu-timestamp, Signature=59d88fae7559e8b1132341f16164a39a4e9e26e2885213151fe6490b35e670a0'  # nopep8
        signature = SignatureV1(self.request, '123ACCESSID', 'SECRET')
        observed = signature._header_value()
        self.assertEqual(observed, expected)

    def test_request_signature(self):
        expected = 'EFU-V1 Credential=123ACCESSID, SignedHeaders=bar;foo;host;x-efu-timestamp, Signature=59d88fae7559e8b1132341f16164a39a4e9e26e2885213151fe6490b35e670a0'  # nopep8
        signature = SignatureV1(self.request, '123ACCESSID', 'SECRET')
        signed_request = signature.sign()
        observed = signed_request.headers.get(
            'Authorization',
            None,
        )
        self.assertIsNotNone(observed)
        self.assertEqual(observed, expected)
