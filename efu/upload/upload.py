# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os
from itertools import count

import click

from ..request import Request

from . import exceptions
from .ui import UploadProgressBar, SUCCESS_MSG, FAIL_MSG


class TransactionExitCode(object):
    SUCCESS = 0
    START_FAIL = 1
    UPLOAD_FAIL = 2
    FINISH_FAIL = 3


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
        self.file_name = self._validate_file(fn)
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
        with open(self.file_name, 'br') as fp:
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
        Uploads a file and returns FileUploadStatus
        '''
        # Check if file exists in server
        if self.exists_in_server:
            return self._finish_upload(UploadStatus.EXISTS, bar)

        # Upload file chunks
        with open(self.file_name, 'rb') as fp:
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


class Package(object):

    def __init__(self, package):
        self._package = self._validate_package(package)
        self.product_id = self._package.get('product_id')
        self.files = [File(fn) for fn in self._package.get('files')]

    def _validate_package(self, filename):
        try:
            with open(filename) as fp:
                package = json.load(fp)
        except FileNotFoundError:
            raise exceptions.InvalidPackageFileError(
                '{} file does not exist'.format(filename)
            )
        except ValueError:
            raise exceptions.InvalidPackageFileError(
                '{} is not a valid JSON file'.format(filename)
            )
        return package


class Transaction(object):

    def __init__(self, package_file):
        self.package = Package(package_file)
        self.product_id = self.package.product_id
        self.files = self.package.files
        self._finish_transaction_url = None

    @property
    def _start_transaction_url(self):
        host = os.environ.get('EFU_SERVER_URL', None)
        if host is None:
            # This must be replaced by the real server URL
            host = 'http://0.0.0.0'
        return '{host}/product/{product_id}/upload/'.format(
            host=host,
            product_id=self.product_id,
        )

    @property
    def _initial_payload(self):
        files = [{'file_id': file.id, 'sha256': file.sha256}
                 for file in self.files]
        payload = json.dumps({
            'product_id': self.product_id,
            'files': files,
        })
        return payload

    def _start_transaction(self):
        request = Request(
            self._start_transaction_url,
            'POST',
            self._initial_payload
        )
        response = request.send()
        if response.status_code != 201:
            raise exceptions.StartTransactionError
        response_body = response.json()
        self._finish_transaction_url = response_body['finish_transaction_url']
        # Injects upload data into self.files
        for f in response_body['files']:
            file = self.files[f['id']]
            file.exists_in_server = f.get('exists', True)
            file.chunk_size = f.get('chunk_size')
            file.part_upload_urls = f.get('urls')
            file.finish_upload_url = f.get('finish_upload_url')

    def _upload_files(self):
        results = []
        for file in self.files:
            n_uploads = len(file.part_upload_urls)
            bar = UploadProgressBar(file.file_name, max=n_uploads)
            results.append(file.upload(bar))
        successful_status = (UploadStatus.SUCCESS, UploadStatus.EXISTS)
        success = [result in successful_status for result in results]
        if not all(success):
            raise exceptions.FileUploadError

    def _finish_transaction(self):
        request = Request(self._finish_transaction_url, 'POST', '')
        response = request.send()
        if response.status_code != 201:
            raise exceptions.FinishTransactionError

    def run(self):
        # START
        try:
            click.echo('Starting transaction: ', nl=False)
            self._start_transaction()
            click.echo(SUCCESS_MSG)
        except exceptions.StartTransactionError:
            click.echo(FAIL_MSG)
            return TransactionExitCode.START_FAIL

        # UPLOAD
        try:
            self._upload_files()
        except exceptions.FileUploadError:
            return TransactionExitCode.UPLOAD_FAIL

        # FINISH
        try:
            click.echo('Finishing transaction: ', nl=False)
            self._finish_transaction()
            click.echo(SUCCESS_MSG)
        except exceptions.FinishTransactionError:
            click.echo(FAIL_MSG)
            return TransactionExitCode.FINISH_FAIL

        return TransactionExitCode.SUCCESS
