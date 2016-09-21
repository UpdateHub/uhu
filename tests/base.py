# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from uuid import uuid4

from efu.config.config import Config
from efu.core import Object, Package
from efu.utils import LOCAL_CONFIG_VAR

from .httpmock.httpd import HTTPMockServer


def delete_environment_variable(var):
    try:
        del os.environ[var]
    except KeyError:
        # variable already deleted
        pass


class BaseMockMixin(object):

    def clean(self):
        pass


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.addCleanup(self.clean)


class ConfigMockMixin(BaseMockMixin):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        _, self.config_filename = tempfile.mkstemp()
        os.environ[Config._ENV_VAR] = self.config_filename
        self.config = Config()

    def clean(self):
        super().clean()
        os.remove(self.config_filename)
        delete_environment_variable(Config._ENV_VAR)


class ObjectMockMixin(BaseMockMixin):

    CHUNK_SIZE = 1

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.set_chunk_size()
        self._files = []

    def clean(self):
        super().clean()
        self.clean_chunk_size()
        self.clean_generated_files()

    def remove_file(self, fn):
        try:
            os.remove(fn)
        except:
            pass  # already deleted

    def set_chunk_size(self):
        os.environ['EFU_CHUNK_SIZE'] = str(self.CHUNK_SIZE)

    def clean_chunk_size(self):
        delete_environment_variable('EFU_CHUNK_SIZE')

    def clean_generated_files(self):
        for file in self._files:
            os.remove(file)
        self._files = []

    def create_file(self, content):
        _, fn = tempfile.mkstemp()
        self._files.append(fn)
        with open(fn, 'bw') as fp:
            fp.write(content)
        return fn


class PackageMockMixin(ObjectMockMixin):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.version = '2.0'
        self.product = '0' * 64
        self.package_id = '1234'

    def create_package_file(self, version, files, product):
        objects = {}
        for obj_id, fn in enumerate(files, 1):
            objects[obj_id] = {
                'filename': fn,
                'mode': 'raw',
                'target-device': 'device'
            }
        content = json.dumps({
            'product': product,
            'version': version,
            'objects': objects,
        }).encode()
        return self.create_file(content=content)


class HTTPServerMockMixin(BaseMockMixin):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.set_server_url()

    @classmethod
    def start_server(cls, simulate_application=False):
        cls.httpd = HTTPMockServer(simulate_application)
        cls.httpd.start()

    @classmethod
    def stop_server(cls):
        cls.httpd.shutdown()

    def clean(self):
        super().clean()
        self.clean_server_url()
        self.httpd.clear_history()

    def set_server_url(self):
        os.environ['EFU_SERVER_URL'] = self.httpd.url('')

    def clean_server_url(self):
        delete_environment_variable('EFU_SERVER_URL')

    def generate_status_code(self, success=True, success_code=201):
        return success_code if success else 400

    def generic_url(self, success, body=None):
        code = self.generate_status_code(success)
        path = '/{}'.format(uuid4().hex)
        self.httpd.register_response(path, 'POST', status_code=code, body=body)
        return self.httpd.url(path)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.start_server()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stop_server()


class UploadMockMixin(PackageMockMixin, HTTPServerMockMixin, ConfigMockMixin):

    def create_upload_meta(self, file, obj_id, file_exists=False,
                           part_exists=False, success=True):
        file.load()
        if success:
            url = self.generic_url(success=True)
        else:
            url = self.generic_url(success=False)

        part_obj = {
            'exists': part_exists,
            'url': url,
        }
        parts = {str(part): part_obj for part in range(file.n_chunks)}
        file_obj = {
            'object_id': obj_id,
            'exists': file_exists,
            'parts': parts,
        }
        return file_obj

    def create_uploads_meta(self, files, **kw):
        return [self.create_upload_meta(fn, obj_id, **kw)
                for obj_id, fn in enumerate(files, 1)]


class PushMockMixin(UploadMockMixin):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.fns = [self.create_file(b'123') for i in range(3)]
        pkg_file = self.create_package_file(
            self.version, self.fns, self.product)
        os.environ[LOCAL_CONFIG_VAR] = pkg_file
        self.package = Package.from_file(pkg_file)
        self.files = list(self.package.objects.values())

    def clean(self):
        super().clean()
        delete_environment_variable(LOCAL_CONFIG_VAR)

    def finish_push_url(self, success=True):
        return self.generic_url(
            success, body=json.dumps({'commit_id': 1}))

    def set_push(self, product, start_success=True,
                 finish_success=True, uploads=None):
        self.httpd.register_response(
            '/products/{}/commits'.format(product),
            method='POST',
            body=json.dumps({
                'uploads': [] if not uploads else uploads,
                'finish_url': self.finish_push_url(finish_success)
            }),
            status_code=self.generate_status_code(start_success)
        )


class PullMockMixin(HTTPServerMockMixin, PackageMockMixin):

    def set_directories(self):
        self._cwd = os.getcwd()
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, self._cwd)
        self.addCleanup(shutil.rmtree, self.dir)

    def set_package_var(self):
        self.pkg_file = os.path.join(self.dir, '.efu')
        os.environ[LOCAL_CONFIG_VAR] = self.pkg_file
        self.addCleanup(os.environ.pop, LOCAL_CONFIG_VAR)

    def set_object(self):
        self.obj_fn = 'image.bin'
        self.obj_id = '1'
        self.obj_content = b'123456789'
        self.obj_sha256sum = hashlib.sha256(self.obj_content).hexdigest()
        self.addCleanup(self.remove_file, self.obj_fn)

    def set_package_id(self):
        self.package_id = '4321'

    def set_urls(self):
        # url to download metadata
        self.httpd.register_response(
            '/products/{}/packages/{}'.format(self.product, self.package_id),
            'GET', body=json.dumps(self.metadata), status_code=200)
        # url to download image
        self.httpd.register_response(
            '/products/{}/objects/{}'.format(
                self.product, self.obj_sha256sum),
            'GET', body=self.obj_content, status_code=200)
