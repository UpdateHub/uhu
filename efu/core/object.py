# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
from itertools import count

from ..metadata import ObjectMetadata
from ..utils import get_chunk_size


class Chunk:

    def __new__(cls, *args):
        ''' Returns None if data (args[0]) is empty '''
        return super().__new__(cls) if args[0] else None

    def __init__(self, data, number):
        self.data = data
        self.number = number
        self.sha256sum = hashlib.sha256(self.data).hexdigest()

    def serialize(self):
        return {
            'sha256sum': self.sha256sum,
            'number': self.number,
        }


class Object:

    def __init__(self, fn, options=None):
        self.filename = fn
        self.options = options
        self.size = None
        self.chunks = []
        self.sha256sum = None
        self.metadata = None
        self.loaded = False

        self._fd = None
        self._chunk_number = count()

    def load(self):
        if self.loaded:
            return
        self._fd = open(self.filename, 'br')
        self.size = os.path.getsize(self.filename)

        sha256sum = hashlib.sha256()
        for chunk in self:
            self.chunks.append(chunk.serialize())
            sha256sum.update(chunk.data)
        self.sha256sum = sha256sum.hexdigest()
        self.metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, self.options)
        self.loaded = True

    def serialize(self):
        self.load()
        return {
            'sha256sum': self.sha256sum,
            'parts': self.chunks,
            'metadata': self.metadata.serialize()
        }

    def _read(self):
        data = self._fd.read(get_chunk_size())
        return Chunk(data, next(self._chunk_number))

    def __iter__(self):
        return iter(self._read, None)

    def __len__(self):
        return len(self.chunks)
