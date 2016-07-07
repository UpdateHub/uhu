# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
from itertools import count

from ..utils import get_chunk_size

from . import exceptions


class File(object):

    _id = count()

    def __init__(self, fn):
        self.id = next(self._id)
        self.name = self._validate_file(fn)
        self.sha256 = self._generate_file_sha256()

        self.exists_in_server = True
        self.part_upload_urls = []
        self.finish_upload_url = None

    def _validate_file(self, fn):
        if os.path.exists(fn):
            return fn
        raise exceptions.InvalidFileError(
            'file {} to be uploaded does not exist'.format(fn)
        )

    def _generate_file_sha256(self):
        sha256 = hashlib.sha256()
        chunk_size = get_chunk_size()
        with open(self.name, 'br') as fp:
            for chunk in iter(lambda: fp.read(chunk_size), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def __reset_id_generator(cls):
        cls._id = count()

    @property
    def n_parts(self):
        return len(self.part_upload_urls)
