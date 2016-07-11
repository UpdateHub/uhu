# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

import click

from ..request import Request
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
        self._finish_push_url = get_server_url(
            response_body['finish_url_path'])

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
        request = Request(self._finish_push_url, 'POST', '')
        response = request.send()
        if response.status_code != 201:
            raise exceptions.FinishPushError

    def run(self):
        # START
        try:
            click.echo('Starting push: ', nl=False)
            self._start_push()
            click.echo(SUCCESS_MSG)
        except exceptions.StartPushError:
            click.echo(FAIL_MSG)
            return PushExitCode.START_FAIL

        # UPLOAD
        try:
            self._upload_files()
        except exceptions.FileUploadError:
            return PushExitCode.UPLOAD_FAIL

        # FINISH
        try:
            click.echo('Finishing push: ', nl=False)
            self._finish_push()
            click.echo(SUCCESS_MSG)
        except exceptions.FinishPushError:
            click.echo(FAIL_MSG)
            return PushExitCode.FINISH_FAIL

        return PushExitCode.SUCCESS
