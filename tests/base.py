# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import tempfile
from random import choice
from datetime import datetime

from efu.upload.upload import File

from .httpmock.utils import BaseHTTPServerTestCase


class BaseTransactionTestCase(BaseHTTPServerTestCase):

    def setUp(self):
        os.environ['EFU_SERVER_URL'] = self.httpd.url('')

    def tearDown(self):
        super().tearDown()
        File._File__reset_id_generator()
        try:
            del os.environ['EFU_SERVER_URL']
        except KeyError:
            # env variable already deleted by other test
            pass

    def _generate_status_code(self, success=True, success_code=201):
        return success_code if success else choice((400, 403, 404, 422, 500))

    def create_empty_file(self, text=False):
        '''
        Helper function which creates an empty temporary file and returns
        its pointer.
        '''
        _, fn = tempfile.mkstemp(text=text)
        self.addCleanup(os.remove, fn)
        return fn

    def register_file_part_upload_path(self, n_parts=1, success=True):
        '''
        Helper function that register n_parts upload part paths.
        '''
        paths = ['/upload/file/1/part/{}/'.format(i) for i in range(n_parts)]
        code = self._generate_status_code(success)
        for path in paths:
            self.httpd.register_response(path, 'POST', status_code=code)
        urls = [self.httpd.url(path) for path in paths]
        return urls

    def register_file_finish_upload_path(self, success=True):
        '''
        Helper function that register a final upload path.
        '''
        path = '/upload/file/1/finish/'
        code = self._generate_status_code(success)
        self.httpd.register_response(path, 'POST', status_code=code)
        url = self.httpd.url(path)
        return url

    def register_start_transaction_path(
            self,
            project_id,
            n_files,
            start_success=True,
            finish_success=True,
            files=[]):
        '''
        Helper function that register a start transaction path.
        '''
        start_path = '/project/{}/upload/'.format(project_id)
        finish_url = self.register_finish_transaction_path(finish_success)
        code = self._generate_status_code(start_success)
        body = json.dumps({
            'finish_transaction_url': finish_url,
            'files': files
        })
        self.httpd.register_response(
            start_path, 'POST', body=body, status_code=code)
        start_url = self.httpd.url(start_path)
        return start_url, finish_url

    def register_finish_transaction_path(self, success=True):
        '''
        Helper function that register a finish transaction path.
        '''
        path = '/project/1/upload/finish/'
        status = 'ok' if success else 'ko'
        code = self._generate_status_code(success)
        self.httpd.register_response(path, 'POST', status_code=code)
        url = self.httpd.url(path)
        return url

    def create_stub_package(self, project_id, n_files):
        '''
        Helper function that generates a stub package file and returns its
        name as also the files created.
        '''
        package_fn = self.create_empty_file()
        files = [self.create_empty_file() for i in range(n_files)]

        with open(package_fn, 'w') as fp:
            obj = {
                'project_id': project_id,
                'files': files
            }
            json.dump(obj, fp)
        return package_fn, files

    def create_existing_file_response(self, file_id):
        '''
        Helper function that generates an empty file response as part of
        start transaction response.

        This must be used as a fixture for a file that already exists
        in server and must not be uploaded.
        '''
        return {
            'id': file_id,
            'exists': True,
            'chunk_size': None,
            'urls': None,
            'finish_upload_url': None,
        }

    def create_non_existing_file_response(
            self, file_id, chunk_size, part_urls, finish_url):
        '''
        Helper function that generates a file response as part of start
        transaction response.

        This must be used as a fixture for a file that does not exist
        in server and must be uploaded.
        '''
        return {
            'id': file_id,
            'exists': False,
            'chunk_size': chunk_size,
            'urls': part_urls,
            'finish_upload_url': finish_url,
        }

    def set_complete_transaction_response(
            self, project_id=1, start_success=True, finish_success=True,
            n_success_files=3, n_existent_files=0, n_fail_files=0,
            chunk_size=1):
        '''
        Helper function that creates all needed responses to complete a
        transaction.
        '''
        files = []
        file_id = 0
        for _ in range(n_success_files):
            files.append(
                self.create_non_existing_file_response(
                    file_id,
                    chunk_size,
                    self.register_file_part_upload_path(),
                    self.register_file_finish_upload_path(),
                )
            )
            file_id += 1

        for _ in range(n_existent_files):
            files.append(self.create_existing_file_response(file_id))
            file_id += 1

        for _ in range(n_fail_files):
            files.append(
                self.create_non_existing_file_response(
                    file_id,
                    chunk_size,
                    self.register_file_part_upload_path(),
                    self.register_file_finish_upload_path(success=False),
                )
            )
            file_id += 1

        n_files = len(files)

        self.register_start_transaction_path(
            project_id, n_files, files=files,
            start_success=start_success, finish_success=finish_success)
        pkg, _ = self.create_stub_package(project_id, n_files)
        return pkg
