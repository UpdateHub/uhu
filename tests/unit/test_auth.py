# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
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

    def test_hashed_canonical_request(self):
        # sha256 of 000 in hex:
        expected = '2ac9a6746aca543af8dff39894cfe8173afba21eb01c6fae33d52947222855ef'  # nopep8
        signature = SignatureV1(self.request, '', '')
        observed = signature._hashed_canonical_request()
        self.assertEqual(observed, expected)

    def test_signed_headers(self):
        expected = 'bar;foo;host;x-efu-timestamp'
        signature = SignatureV1(self.request, '', '')
        observed = signature._signed_headers()
        self.assertEqual(observed, expected)

    def test_message(self):
        '''
        The expected value here is a string with 3 lines. The first line
        is the signature version. The second line is the request
        timestamp. And the third line is a sha256 hash of the
        canonical request in hexadecimal format. In this test, the
        value hashed was 000.
        '''
        expected = '''EFU-V1
1
2ac9a6746aca543af8dff39894cfe8173afba21eb01c6fae33d52947222855ef'''
        signature = SignatureV1(self.request, '', '')
        observed = signature._message()
        self.assertEqual(observed, expected)

    def test_key(self):
        '''
        The expected value here is a hmac-sha256 hash in hexadecimal using
        EFU-V1-SECRET as key and 1 as message.

        In pseudo code it would be:

        key = EFU-V1-SECRET
        msg = 1
        hex(hmac-sha256(key, msg))
        '''
        expected = '1a0b1127ff608b026c90bdc5c44200d8bf5287278e8d48d5983949869c26cb4f'  # nopep8
        signature = SignatureV1(self.request, '', 'SECRET')
        observed = signature._key()
        self.assertEqual(observed, expected)

    def test_signature_hash(self):
        '''
        The expected hash here comes from the previous generated ones. It
        is a hmac-sha256 using as key the expected value from the
        test_key method and as message the expected value from the
        test_message method.
        '''
        expected = '3e9d0bb3df49a1243201258d6390ddddeb6654ac722992cd9198d84f637e5929'  # nopep8
        signature = SignatureV1(self.request, '', 'SECRET')
        observed = signature._signature_hash()
        self.assertEqual(observed, expected)

    def test_final_signature(self):
        '''
        The signature hash used here is the same from test_signature method
        '''
        expected = 'EFU-V1 Credential=123ACCESSID/1, SignedHeaders=bar;foo;host;x-efu-timestamp, Signature=3e9d0bb3df49a1243201258d6390ddddeb6654ac722992cd9198d84f637e5929'  # nopep8
        signature = SignatureV1(self.request, '123ACCESSID', 'SECRET')
        observed = signature.signature
        self.assertEqual(observed, expected)
