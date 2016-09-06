# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..http.request import Request
from ..utils import get_server_url

from . import exceptions
from .ui import SUCCESS_MSG, FAIL_MSG
from .upload import Upload, UploadStatus


class PushExitCode(object):
    SUCCESS = 0
    START_FAIL = 1
    UPLOAD_FAIL = 2
    FINISH_FAIL = 3


class Push(object):

    def __init__(self, package):
        self._package = package
        self._upload_list = None
        self._finish_push_url = None
        self._commit_id = None

    @property
    def _start_push_url(self):
        return get_server_url(
            '/products/{}/commits'.format(self._package.product_id))

    def _start_push(self):
        request = Request(
            self._start_push_url,
            method='POST',
            payload=json.dumps(self._package.as_dict()),
            json=True,
        )
        response = request.send()
        if response.status_code != 201:
            raise exceptions.StartPushError

        response_body = response.json()
        self._upload_list = {upload['object_id']: upload
                             for upload in response_body['uploads']}
        self._finish_push_url = response_body['finish_url']

    def _upload_files(self):
        results = []
        for file_id, meta in self._upload_list.items():
            file = self._package.files[file_id]
            result = Upload(file, meta, progress=True).upload()
            results.append(result)
        successful_status = (UploadStatus.SUCCESS, UploadStatus.EXISTS)
        success = [result in successful_status for result in results]
        if not all(success):
            raise exceptions.FileUploadError

    def _finish_push(self):
        request = Request(self._finish_push_url, 'POST')
        response = request.send()
        if response.status_code != 201:
            raise exceptions.FinishPushError
        self._commit_id = response.json().get('commit_id')

    def run(self):
        # START
        try:
            print('Starting push: ', end='')
            self._start_push()
            print(SUCCESS_MSG)
        except exceptions.StartPushError:
            print(FAIL_MSG)
            return PushExitCode.START_FAIL

        # UPLOAD
        try:
            self._upload_files()
        except exceptions.FileUploadError:
            return PushExitCode.UPLOAD_FAIL

        # FINISH
        try:
            print('Finishing push: ', end='')
            self._finish_push()
            print(SUCCESS_MSG)
            print('Commit ID: {}'.format(self._commit_id))
        except exceptions.FinishPushError:
            print(FAIL_MSG)
            return PushExitCode.FINISH_FAIL

        return PushExitCode.SUCCESS
