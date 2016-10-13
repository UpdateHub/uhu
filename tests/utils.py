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

    def generic_url(self, success, body=None, method='POST'):
        code = self.generate_status_code(success)
        path = '/{}'.format(uuid4().hex)
        self.httpd.register_response(path, method, status_code=code, body=body)
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

    def create_upload_conf(self, obj, product_uid, package_uid, exists=False,
                           start_success=True, upload_success=True):
        upload_url = self.generic_url(upload_success, method='PUT')

        start_upload_path = '/products/{}/packages/{}/objects/{}'.format(
            product_uid, package_uid, obj.sha256sum)
        start_upload_url = self.httpd.url(start_upload_path)
        start_upload_body = json.dumps({
            'url': upload_url,
            'storage': 'dummy',
        })
        start_upload_code = 200 if exists else 201
        start_upload_code = start_upload_code if start_success else 400
        self.httpd.register_response(
            start_upload_path, 'POST', body=start_upload_body,
            status_code=start_upload_code)


class PushFixtureMixin:

    def set_push(self, package, package_uid, start_success=True,
                 upload_success=True, upload_start_success=True,
                 upload_exists=False, finish_success=True):
        self.start_push_url(package.product, package_uid, start_success)
        for obj in package:
            obj.load()
            self.create_upload_conf(
                obj, package.product, package_uid, upload_exists,
                upload_start_success, upload_success)
        self.finish_push_url(package.product, package_uid, finish_success)

    def start_push_url(self, product, package_uid, success=True):
        path = '/products/{}/packages'.format(product)
        code = self.generate_status_code(success)
        if success:
            body = {'package-uid': package_uid}
        else:
            body = {'errors': ['This is an error', 'And this is another one']}
        self.httpd.register_response(
            path, method='POST', body=json.dumps(body), status_code=code)

    def finish_push_url(self, product, package_uid, success=True):
        path = '/products/{}/packages/{}/finish'.format(product, package_uid)
        code = self.generate_status_code(success, 202)
        if success:
            body = ''
        else:
            body = json.dumps(
                {'errors': ['This is an error', 'And this is another one']})
        self.httpd.register_response(
            path, method='POST', body=body, status_code=code)
