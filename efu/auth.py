# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import hmac


class SignatureV1(object):
    '''
    This signature uses the hmac-sha256 hash algorithm to generate the
    final signature.

    The main point in this signature is that both key and message are
    generated based on the request and user credentials.
    '''

    def __init__(self, request, access_id, secret):
        self._request = request
        self._access_id = access_id
        self._secret = secret
        self._timestamp = str(self._request.timestamp)

    def _hashed_canonical_request(self):
        cr = self._request.canonical()
        return hashlib.sha256(cr.encode()).hexdigest()

    def _signed_headers(self):
        '''
        Generates a string listing alphabetically all the headers included
        in the canonical request.

        The returned value will be included in the Authorization
        header so the server may recreates the signature.
        '''
        headers = [header.lower() for header in self._request.headers.keys()]
        return ';'.join(sorted(headers))

    def _message(self):
        '''
        Generates the message to be signed.
        '''
        return 'EFU-V1\n{timestamp}\n{canonical_request}'.format(
            timestamp=self._request.timestamp,
            canonical_request=self._hashed_canonical_request(),
        )

    def _key(self):
        '''
        Generates the key to sign the final message.
        '''
        base_key = 'EFU-V1-{}'.format(self._secret)
        final_key = hmac.new(
            base_key.encode(),
            self._timestamp.encode(),
            'sha256',
        )
        return final_key.hexdigest()

    def _signature_hash(self):
        '''
        Generates the signature using hmac-sha256 with the already
        computed key and message.
        '''
        signature = hmac.new(
            self._key().encode(),
            self._message().encode(),
            'sha256'
        )
        return signature.hexdigest()

    @property
    def signature(self):
        '''
        Creates the value for the Authorization header.
        '''
        header = 'EFU-V1 Credential={}/{}, SignedHeaders={}, Signature={}'
        return header.format(
            self._access_id,
            self._timestamp,
            self._signed_headers(),
            self._signature_hash(),
        )
