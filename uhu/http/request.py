# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import hashlib
from datetime import datetime, timezone
from urllib.parse import quote, urlparse, parse_qs

import requests

from .. import get_version
from ..config import config

from .auth import UHV1Signature


class Request(object):

    def __init__(self, url, method, payload='', json=False, **requests_kwargs):
        self.url = url
        self._url = urlparse(self.url)
        self.method = method.upper()
        self.payload = payload
        self._requests_kwargs = requests_kwargs

        self.date = datetime.now(timezone.utc)
        self.payload_sha256 = self._generate_payload_sha256()

        self.headers = {
            'User-Agent': 'updatehub-utils/{}'.format(get_version()),
            'Host': self._url.netloc,
            'Timestamp': self.date.timestamp(),
            'Content-sha256': self.payload_sha256,
            'Api-Content-Type': 'application/vnd.updatehub-v1+json',
            'Accept': 'application/json',
        }
        if json:
            self.headers['Content-Type'] = 'application/json'

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
        signature = UHV1Signature(self, access_id, access_secret)
        self.headers['Authorization'] = signature.signature

    def _prepare_headers(self):
        """Transforms all header values in strings.

        This must be called before any real HTTP request to prevent
        breaking any library that just expects strings as header
        values.
        """
        return {header: str(self.headers[header]) for header in self.headers}

    def send(self):
        self._sign()
        headers = self._prepare_headers()
        response = requests.request(
            self.method,
            self.url,
            headers=headers,
            data=self.payload,
            **self._requests_kwargs
        )
        return response
