# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..request import Request
from ..utils import get_chunk_size

from .ui import UploadProgressBar, SUCCESS_MSG, FAIL_MSG


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


class Upload(object):

    def __init__(self, file, progress=False):
        self._file = file

        self._bar = None
        if progress:
            self._bar = UploadProgressBar(
                self._file.name, max=self._file.n_parts)

    def upload(self):
        '''
        Uploads a file and returns UploadStatus
        '''
        # Check if file exists in server
        if self._file.exists_in_server:
            return self._finish_upload(UploadStatus.EXISTS)

        # Upload file chunks
        with open(self._file.name, 'rb') as fp:
            for url in self._file.part_upload_urls:
                payload = fp.read(get_chunk_size())
                response = Request(url, 'POST', payload).send()
                if response.status_code != 201:
                    return self._finish_upload(UploadStatus.PART_FAIL)
                self._increase_bar_progress()

        # Finish upload
        response = Request(self._file.finish_upload_url, 'POST', '').send()
        if response.status_code == 201:
            status = UploadStatus.SUCCESS
        else:
            status = UploadStatus.FAIL
        return self._finish_upload(status)

    def _finish_upload(self, status):
        if self._bar is not None:
            self._bar.finish_with_msg(UploadStatus.MESSAGES[status])
        return status

    def _increase_bar_progress(self):
        if self._bar is not None:
            self._bar.next()
