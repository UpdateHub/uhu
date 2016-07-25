# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
from itertools import count

from ..utils import get_chunk_size

from . import exceptions


class FileChunk(object):

    def __new__(cls, *args):
        ''' Returns None if data (args[0]) is empty '''
        return super().__new__(cls) if args[0] else None

    def __init__(self, data, number):
        self.data = data
        self.number = number
        self.sha256sum = hashlib.sha256(self.data).hexdigest()

    def as_dict(self):
        return {
            'sha256sum': self.sha256sum,
            'number': self.number,
        }


class File(object):

    _id = count()

    def __new__(cls, fn):
        if os.path.isfile(fn):
            return super().__new__(cls)
        raise exceptions.InvalidFileError(
            'file {} does not exist'.format(fn))

    def __init__(self, fn):
        self.id = next(self._id)
        self._chunk_number = count()
        self._file = open(fn, 'br')
        self.name = fn
        self.size = os.path.getsize(self.name)
        self.chunks = []

        sha256sum = hashlib.sha256()
        for chunk in self:
            self.chunks.append(chunk)
            sha256sum.update(chunk.data)
        self.sha256sum = sha256sum.hexdigest()

    def as_dict(self):
        return {
            'id': self.id,
            'sha256sum': self.sha256sum,
            'parts': [chunk.as_dict() for chunk in self.chunks],
            'metadata': self.metadata
        }

    @property
    def metadata(self):
        return {
            'filename': self.name,
            'sha256sum': self.sha256sum,
            'size': self.size
        }

    @property
    def n_chunks(self):
        return len(self.chunks)

    @classmethod
    def __reset_id_generator(cls):
        cls._id = count()

    def _read(self):
        data = self._file.read(get_chunk_size())
        return FileChunk(data, next(self._chunk_number))

    def __iter__(self):
        return iter(self._read, None)
