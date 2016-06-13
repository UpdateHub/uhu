# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from datetime import datetime
import hashlib
from urllib.parse import quote, urlparse, parse_qs

from .auth import SignatureV1
from .config import config


class Request(object):

    def __init__(self, url, method, payload):
        self.url = url
        self._url = urlparse(self.url)
        self.method = method.upper()
        self.payload = payload

        self.date = datetime.utcnow()
        self.timestamp = self.date.timestamp()
        self.payload_sha256 = self._generate_payload_sha256()

        self.headers = {
            'Host': self._url.hostname,
            'Timestamp': self.timestamp,
            'Content-sha256': self.payload_sha256,
        }

    def _generate_payload_sha256(self):
        payload = self.payload
        if not isinstance(payload, bytes):
            payload = payload.encode()
        return hashlib.sha256(payload).hexdigest()

    def _canonical_query(self):
        raw_query = parse_qs(self._url.query)
        query = []
        for key in raw_query:
            for value in sorted(raw_query[key]):
                query.append('{}={}'.format(key, quote(value)))
        return '&'.join(sorted(query))

    def _canonical_headers(self):
        normalized_headers = [(k.strip().lower(), str(v).strip())
                              for k, v in self.headers.items()]
        headers = ['{}:{}'.format(header, value)
                   for header, value in normalized_headers]
        return '\n'.join(sorted(headers))

    def canonical(self):
        request = '{method}\n{uri}\n{query}\n{headers}\n\n{payload}'
        return request.format(
            method=self.method,
            uri=self._url.path,
            query=self._canonical_query(),
            headers=self._canonical_headers(),
            payload=self.payload_sha256,
        )

    def _sign(self):
        access_id = config.get('access_id', section='auth')
        access_secret = config.get('access_secret', section='auth')
        signature = SignatureV1(self, access_id, access_secret)
        self.headers['Authorization'] = signature.signature
