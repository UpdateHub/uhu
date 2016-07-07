# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import itertools
import math
import os
import tempfile
from random import choice

from efu.config.config import Config
from efu.upload.upload import File

from .httpmock.utils import BaseHTTPServerTestCase


def delete_environment_variable(var):
    try:
        del os.environ[var]
    except KeyError:
        # variable already deleted
        pass


class ServerMocker(object):

    def __init__(self, httpd):
        self.httpd = httpd
        self.files = []

    def _generate_status_code(self, success=True, success_code=201):
        return success_code if success else choice((400, 403, 404, 422, 500))

    def set_server_url(self):
        os.environ['EFU_SERVER_URL'] = self.httpd.url('')

    def clean_generated_files(self):
        for file in self.files:
            os.remove(file)
        self.files = []

    def clean_server_url(self):
        delete_environment_variable('EFU_SERVER_URL')

    def clean_file_id_generator(self):
        File._File__reset_id_generator()

    def create_file(self, content):
        '''
        Helper function which creates an empty temporary file and returns
        its pointer.
        '''
        _, fn = tempfile.mkstemp()
        self.files.append(fn)
        with open(fn, 'bw') as fp:
            fp.write(content)
        return fn

    def register_finish_transaction_url(self, product_id, success=True):
        '''
        Helper function that register a finish transaction path.
        '''
        path = '/product/{}/upload/finish/'.format(product_id)
        code = self._generate_status_code(success)
        self.httpd.register_response(path, 'POST', status_code=code)
        return self.httpd.url(path)

    def register_start_transaction_url(
            self, product_id, files,
            start_success=True, finish_success=True):
        '''
        Helper function that register a start transaction path.
        '''
        start_path = '/product/{}/upload/'.format(product_id)
        code = self._generate_status_code(start_success)
        finish_url = self.register_finish_transaction_url(
            product_id, finish_success)
        body = json.dumps({
            'finish_transaction_url': finish_url,
            'files': files
        })
        self.httpd.register_response(
            start_path, 'POST', body=body, status_code=code)
        return (self.httpd.url(start_path), finish_url)

    def register_file_part_upload_urls(
            self, product_id, file_id, n_parts, success=True):
        '''
        Helper function that register n_parts upload part paths.
        '''
        path = '/product/{}/upload/file/{}/part/{}/'
        paths = [path.format(product_id, file_id, i) for i in range(n_parts)]
        code = self._generate_status_code(success)
        for path in paths:
            self.httpd.register_response(path, 'POST', status_code=code)
        return [self.httpd.url(path) for path in paths]

    def register_file_finish_upload_url(
            self, product_id, file_id, success=True):
        '''
        Helper function that register a final upload path.
        '''
        path = '/product/{}/upload/file/{}/finish/'.format(product_id, file_id)
        code = self._generate_status_code(success)
        self.httpd.register_response(path, 'POST', status_code=code)
        return self.httpd.url(path)

    def set_file(self, product_id, file_id, content=b'0', chunk_size=1,
                 part_success=True, finish_success=True, exists=False):
        '''
        Helper function that creates a file in file system and sets the
        server responses to deal with its upload.
        '''
        file = self.create_file(content=content)
        n_parts = math.ceil(len(content) / chunk_size)
        part_urls = self.register_file_part_upload_urls(
            product_id, file_id, n_parts, part_success)
        finish_url = self.register_file_finish_upload_url(
            product_id, file_id, finish_success)
        response = {
            'id': file_id,
            'exists': exists,
            'chunk_size': chunk_size,
            'urls': part_urls,
            'finish_upload_url': finish_url,
        }
        return (file, response)

    def set_package(self, product_id, files):
        '''
        Helper function that generates a stub package.
        '''
        content = json.dumps({
            'product_id': product_id,
            'files': files,
        }).encode()
        pkg = self.create_file(content=content)
        return pkg

    def set_transaction(self, product_id, file_size=1, chunk_size=1,
                        start_success=True, finish_success=True,
                        success_files=3, existent_files=0,
                        finish_fail_files=0, part_fail_files=0):
        '''
        Helper function that creates all needed responses to complete an
        upload transaction.
        '''
        files = []
        responses = []
        file_id = itertools.count()
        content = file_size * b'0'
        for _ in range(success_files):
            fn, response = self.set_file(
                product_id, next(file_id), content, chunk_size=chunk_size)
            files.append(fn)
            responses.append(response)
        for _ in range(existent_files):
            fn, response = self.set_file(
                product_id, next(file_id), exists=True)
            files.append(fn)
            responses.append(response)
        for _ in range(part_fail_files):
            fn, response = self.set_file(
                product_id, next(file_id), content, chunk_size=chunk_size,
                part_success=False)
            files.append(fn)
            responses.append(response)
        for _ in range(finish_fail_files):
            fn, response = self.set_file(
                product_id, next(file_id), content, chunk_size=chunk_size,
                finish_success=False)
            files.append(fn)
            responses.append(response)

        self.register_start_transaction_url(
            product_id, responses, start_success=start_success,
            finish_success=finish_success)
        pkg = self.set_package(product_id, files)
        return pkg


class ConfigTestCaseMixin(object):

    def setUp(self):
        super().setUp()
        _, self.config_filename = tempfile.mkstemp()
        os.environ[Config._ENV_VAR] = self.config_filename
        self.addCleanup(os.remove, self.config_filename)
        self.addCleanup(delete_environment_variable, Config._ENV_VAR)
        self.config = Config()


class BaseTransactionTestCase(ConfigTestCaseMixin, BaseHTTPServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fixture = ServerMocker(cls.httpd)

    def setUp(self):
        super().setUp()
        self.addCleanup(self.fixture.clean_generated_files)
        self.fixture.set_server_url()

    def tearDown(self):
        super().tearDown()
        self.fixture.clean_server_url()
        self.fixture.clean_file_id_generator()
