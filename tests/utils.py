# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os
import tempfile
import unittest
from uuid import uuid4

from .httpmock.httpd import HTTPMockServer


class HTTPTestCaseMixin:

    @classmethod
    def start_server(cls, simulate_application=False):
        cls.httpd = HTTPMockServer(simulate_application)
        cls.httpd.start()

    @classmethod
    def stop_server(cls):
        cls.httpd.shutdown()

    def generate_status_code(self, success=True, success_code=201):
        return success_code if success else 400

    def generic_url(self, success, body=None):
        code = self.generate_status_code(success)
        path = '/{}'.format(uuid4().hex)
        self.httpd.register_response(path, 'POST', status_code=code, body=body)
        return self.httpd.url(path)

    def clean(self):
        super().clean()
        self.httpd.clear_history()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.start_server()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stop_server()


class EFUTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.clean)

    def clean(self):
        pass


class FileFixtureMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._files = []

    def create_file(self, content=None):
        if not isinstance(content, bytes):
            content = content.encode()
        _, fn = tempfile.mkstemp()
        self._files.append(fn)
        with open(fn, 'bw') as fp:
            fp.write(content)
        return fn

    def remove_file(self, fn):
        try:
            os.remove(fn)
        except FileNotFoundError:
            pass  # already deleted

    def sha256sum(self, data):
        return hashlib.sha256(data).hexdigest()

    def clean(self):
        super().clean()
        while self._files:
            self.remove_file(self._files.pop())


class EnvironmentFixtureMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vars = []

    def remove_env_var(self, var):
        try:
            del os.environ[var]
        except KeyError:
            pass  # already deleted

    def set_env_var(self, var, value):
        self._vars.append(var)
        os.environ[var] = str(value)

    def clean(self):
        super().clean()
        for var in self._vars:
            self.remove_env_var(var)


class UploadFixtureMixin:

    def create_upload_conf(self, obj, obj_exists=False,
                           chunk_exists=False, success=True):
        url = self.generic_url(success=success)
        chunk_conf = {
            'exists': chunk_exists,
            'url': url,
        }
        chunks = {str(chunk): chunk_conf for chunk in range(len(obj))}
        obj_conf = {
            'object_id': obj.uid,
            'exists': obj_exists,
            'chunks': chunks,
        }
        return obj_conf


class PushFixtureMixin:

    def set_push(self, product, start_success=True,
                 finish_success=True, uploads=None):
        self.httpd.register_response(
            '/products/{}/packages'.format(product),
            method='POST',
            body=json.dumps({
                'uploads': [] if not uploads else uploads,
                'finish_url': self.finish_push_url(finish_success)
            }),
            status_code=self.generate_status_code(start_success)
        )

    def finish_push_url(self, success=True):
        return self.generic_url(
            success, body=json.dumps({'package_id': 1}))

    def create_package_uploads(self, package, **kwargs):
        package.load()
        return [self.create_upload_conf(obj, **kwargs) for obj in package]
