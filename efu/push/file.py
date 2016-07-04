# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
from itertools import count

from ..request import Request

from . import exceptions
from .ui import SUCCESS_MSG, FAIL_MSG


class UploadStatus(object):
    SUCCESS = 0
    EXISTS = 1
    PART_FAIL = 2
    FAIL = 3

    MESSAGES = {
        SUCCESS: SUCCESS_MSG,
        EXISTS: '{} (already uploaded)'.format(SUCCESS_MSG),
        PART_FAIL: '{} (upload part error)'.format(FAIL_MSG),
        FAIL: '{} (upload error)'.format(FAIL_MSG),
    }


class File(object):

    _id = count()

    def __init__(self, fn):
        self.id = next(self._id)
        self.name = self._validate_file(fn)
        self.sha256 = self._generate_file_sha256()

        self.exists_in_server = True
        self.part_upload_urls = []
        self.finish_upload_url = None
        self.chunk_size = None

    def _validate_file(self, fn):
        if os.path.exists(fn):
            return fn
        raise exceptions.InvalidFileError(
            'file {} to be uploaded does not exist'.format(fn)
        )

    def _generate_file_sha256(self):
        sha256 = hashlib.sha256()
        chunk_size = 1024 ** 2 * 5  # 5 Mib
        with open(self.name, 'br') as fp:
            for chunk in iter(lambda: fp.read(chunk_size), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def __reset_id_generator(cls):
        cls._id = count()

    def _finish_upload(self, status, bar):
        if bar is not None:
            bar.finish_with_msg(UploadStatus.MESSAGES[status])
        return status

    def _increase_bar_progress(self, bar):
        if bar is not None:
            bar.next()

    def upload(self, bar=None):
        '''
        Uploads a file and returns UploadStatus
        '''
        # Check if file exists in server
        if self.exists_in_server:
            return self._finish_upload(UploadStatus.EXISTS, bar)

        # Upload file chunks
        with open(self.name, 'rb') as fp:
            for url in self.part_upload_urls:
                payload = fp.read(self.chunk_size)
                response = Request(url, 'POST', payload).send()
                if response.status_code != 201:
                    return self._finish_upload(UploadStatus.PART_FAIL, bar)
                self._increase_bar_progress(bar)

        # Finish upload
        response = Request(self.finish_upload_url, 'POST', '').send()
        if response.status_code == 201:
            status = UploadStatus.SUCCESS
        else:
            status = UploadStatus.FAIL
        return self._finish_upload(status, bar)
