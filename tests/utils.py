# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from uuid import uuid4

from efu.core import Package
from efu.core.installation_set import InstallationSetMode
from efu.utils import CHUNK_SIZE_VAR, LOCAL_CONFIG_VAR, SERVER_URL_VAR

from httpmock.httpd import HTTPMockServer


class HTTPTestCaseMixin:

    @classmethod
    def start_server(cls, port=0, simulate_application=False):
        cls.httpd = HTTPMockServer(port, simulate_application)
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
        for obj in package.objects.all():
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


class BasePushTestCase(
        PushFixtureMixin, UploadFixtureMixin, EnvironmentFixtureMixin,
        FileFixtureMixin, HTTPTestCaseMixin, EFUTestCase):

    def setUp(self):
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        self.product = '0' * 64
        self.version = '2.0'
        self.package_uid = '1' * 64
        self.package = Package(
            InstallationSetMode.Single, version=self.version,
            product=self.product)
        for _ in range(3):
            fn = self.create_file('123')
            self.package.objects.create(
                fn, 'raw', {'target-device': '/dev/sda'})


class BasePullTestCase(EnvironmentFixtureMixin, FileFixtureMixin,
                       HTTPTestCaseMixin, EFUTestCase):

    def setUp(self):
        wd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, wd)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(wd)

        self.pkg_fn = os.path.join(wd, 'efu')
        self.set_env_var(LOCAL_CONFIG_VAR, self.pkg_fn)

        self.product = 'product-uid'
        self.pkg_uid = 'package-uid'
        self.package = Package(
            InstallationSetMode.Single, product=self.product)

        # object
        self.obj_fn = 'image.bin'
        self.obj_content = b'spam'
        self.obj_sha256 = hashlib.sha256(self.obj_content).hexdigest()
        self.addCleanup(self.remove_file, self.obj_fn)

        self.metadata = {
            'product': self.product,
            'version': '2.0',
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'target-device': '/device',
                        'size': 4,
                        'sha256sum': hashlib.sha256(
                            self.obj_content).hexdigest()
                    }
                ]
            ]
        }

        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        # url to download metadata
        self.httpd.register_response(
            '/packages/{}'.format(self.pkg_uid),
            'GET', body=json.dumps(self.metadata), status_code=200)

        # url to download object
        path = '/products/{}/packages/{}/objects/{}'.format(
            self.product, self.pkg_uid, self.obj_sha256)
        self.httpd.register_response(
            path, 'GET', body=self.obj_content, status_code=200)
