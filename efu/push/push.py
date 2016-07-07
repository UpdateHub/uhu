# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

import click

from ..request import Request
from ..utils import get_server_url

from . import exceptions
from .ui import SUCCESS_MSG, FAIL_MSG
from .package import Package
from .upload import Upload, UploadStatus


class PushExitCode(object):
    SUCCESS = 0
    START_FAIL = 1
    UPLOAD_FAIL = 2
    FINISH_FAIL = 3


class Push(object):

    def __init__(self, package_file):
        self.package = Package(package_file)
        self.product_id = self.package.product_id
        self.files = self.package.files
        self._finish_push_url = None

    @property
    def _start_push_url(self):
        return get_server_url('/product/{}/upload/'.format(self.product_id))

    @property
    def _initial_payload(self):
        files = [{'file_id': file.id, 'sha256': file.sha256}
                 for file in self.files]
        payload = json.dumps({
            'product_id': self.product_id,
            'files': files,
        })
        return payload

    def _start_push(self):
        request = Request(
            self._start_push_url,
            'POST',
            self._initial_payload
        )
        response = request.send()
        if response.status_code != 201:
            raise exceptions.StartPushError
        response_body = response.json()
        self._finish_push_url = response_body['finish_push_url']
        # Injects upload data into self.files
        for f in response_body['files']:
            file = self.files[f['id']]
            file.exists_in_server = f.get('exists', True)
            file.part_upload_urls = f.get('urls')
            file.finish_upload_url = f.get('finish_upload_url')

    def _upload_files(self):
        results = [Upload(file, progress=True).upload() for file in self.files]
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
