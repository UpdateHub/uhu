# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import hmac


class UHV1Signature:  # pylint: disable=too-few-public-methods
    """UpdateHub server Signature V1.

    This signature uses the hmac-sha256 hash algorithm to generate the
    final signature.

    The main point in this signature is that both key and message are
    generated based on the request and user credentials.
    """

    def __init__(self, request, access_id, secret):
        self._request = request
        self._access_id = access_id
        self._secret = secret

    def _hashed_canonical_request(self):
        canonical_request = self._request.canonical()
        return hashlib.sha256(canonical_request.encode()).hexdigest()

    def _signed_headers(self):
        """Generates the signed headers.

        Generates a string listing alphabetically all the headers
        included in the canonical request.

        The returned value will be included in the Authorization
        header so the server may recreates the signature.
        """
        headers = [header.lower() for header in self._request.headers.keys()]
        return ';'.join(sorted(headers))

    def _message(self):
        """Generates the message to be signed.

        Its a string based on the server authentication algorithm name
        and version, the request timestamp in ISO-8601 format and the
        canonical request. Each of these values are separated by a
        line break:

        {auth_name}-{auth-version}
        {request_timestamp}
        {canonical_request}
        """
        timestamp = self._request.date.strftime('%Y%m%dT%H%M%SZ')
        return 'UH-V1\n{timestamp}\n{canonical_request}'.format(
            timestamp=timestamp,
            canonical_request=self._hashed_canonical_request(),
        )

    def _key(self):
        """Generates the key to sign the final message.

        The key is a hexadecimal hash generated with hmac-sha256 using
        base_key as key and the request_date as message:

        key = hex(hmac-256(base_key, message))

        --------
        Base key
        --------

        Base key is the concatenation of the name and version of server
        authentication algorithm plus the user secret:

        {auth_name}-{auth_version}-{user_secret}

        If the authentication algorithm name is UH, the version is
        V1 and the user secret is 123, the base key is:

        base_key = 'UH-V1-123'

        ------------
        Request date
        ------------

        The request date used as message in the hmac algorithm must be
        in the YYYYMMDD format:

        message = '19991231'
        """
        base_key = 'UH-V1-{}'.format(self._secret).encode()
        request_date = self._request.date.strftime('%Y%m%d').encode()
        final_key = hmac.new(base_key, request_date, 'sha256')
        return final_key.hexdigest()

    def _signature_hash(self):
        """Generates the final signature.

        Generates the signature using hmac-sha256 with the already
        computed key and message.
        """
        signature = hmac.new(
            self._key().encode(),
            self._message().encode(),
            'sha256'
        )
        return signature.hexdigest()

    @property
    def signature(self):
        """Creates the value for the Authorization header."""
        header = 'UH-V1 Credential={}, SignedHeaders={}, Signature={}'
        return header.format(
            self._access_id,
            self._signed_headers(),
            self._signature_hash(),
        )
