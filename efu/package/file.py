# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
from itertools import count

from ..utils import get_chunk_size

from . import exceptions


class FileChunk(object):

    _number = count()

    def __new__(cls, chunk):
        return super().__new__(cls) if chunk else None

    def __init__(self, chunk):
        self.data = chunk
        self.number = next(self._number)
        self.sha256sum = hashlib.sha256(chunk).hexdigest()

    def as_dict(self):
        return {
            'sha256sum': self.sha256sum,
            'number': self.number,
        }

    @classmethod
    def reset_number_generator(cls):
        cls._number = count()


class File(object):

    _id = count()

    def __new__(cls, fn):
        if os.path.isfile(fn):
            return super().__new__(cls)
        raise exceptions.InvalidFileError(
            'file {} does not exist'.format(fn))

    def __init__(self, fn):
        self.id = next(self._id)
        self._file = open(fn, 'br')
        self.name = fn
        self.size = os.path.getsize(self.name)
        self.chunks = []

        sha256sum = hashlib.sha256()
        for chunk in self:
            self.chunks.append(chunk)
            sha256sum.update(chunk.data)
        self.sha256sum = sha256sum.hexdigest()

        FileChunk.reset_number_generator()

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

    def __iter__(self):
        return iter(lambda: FileChunk(self._file.read(get_chunk_size())), None)
