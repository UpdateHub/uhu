# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..http.request import Request
from ..utils import get_chunk_size

from .ui import UploadProgressBar, SUCCESS_MSG, FAIL_MSG


class UploadStatus(object):
    SUCCESS = 0
    EXISTS = 1
    FAIL = 3

    MESSAGES = {
        SUCCESS: SUCCESS_MSG,
        EXISTS: '{} (already uploaded)'.format(SUCCESS_MSG),
        FAIL: '{} (upload error)'.format(FAIL_MSG),
    }


class Upload(object):

    def __init__(self, file, upload_meta, progress=False):
        self._file = file
        self._already_uploaded = upload_meta['exists']
        self._parts_meta = upload_meta['parts']

        self._bar = None
        if progress:
            self._bar = UploadProgressBar(
                self._file.name, max=self._file.n_chunks)

    def upload(self):
        '''
        Uploads a file and returns UploadStatus
        '''
        # Check if file exists in server
        if self._already_uploaded:
            return self._finish_upload(UploadStatus.EXISTS)

        # Upload file chunks
        status = UploadStatus.SUCCESS
        with open(self._file.name, 'rb') as fp:
            parts = iter(lambda: fp.read(get_chunk_size()), b'')
            for part_number, part in enumerate(parts):
                part_meta = self._parts_meta[str(part_number)]
                if not part_meta['exists']:
                    url = part_meta['url']
                    response = Request(url, 'POST', part).send()
                    if response.status_code != 201:
                        status = UploadStatus.FAIL
                self._increase_bar_progress()
        return self._finish_upload(status)

    def _finish_upload(self, status):
        if self._bar is not None:
            self._bar.finish_with_msg(UploadStatus.MESSAGES[status])
        return status

    def _increase_bar_progress(self):
        if self._bar is not None:
            self._bar.next()
