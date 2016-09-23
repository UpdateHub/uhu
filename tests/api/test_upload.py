# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.core import Object
from efu.core.object import ObjectUploadResult
from efu.utils import CHUNK_SIZE_VAR, SERVER_URL_VAR

from ..utils import (
    EFUTestCase, EnvironmentFixtureMixin, FileFixtureMixin,
    HTTPTestCaseMixin, UploadFixtureMixin)


class UploadTestCase(
        UploadFixtureMixin, EnvironmentFixtureMixin, FileFixtureMixin,
        HTTPTestCaseMixin, EFUTestCase):

    def setUp(self):
        super().setUp()
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        self.obj_fn = self.create_file(b'spam')
        self.obj = Object(1, self.obj_fn, 'raw', {'target-device': 'raw'})
        self.obj.load()

    def test_returns_success_when_upload_is_successful(self):
        conf = self.create_upload_conf(self.obj)
        result = self.obj.upload(conf)
        self.assertEqual(result, ObjectUploadResult.SUCCESS)

    def test_does_not_upload_when_file_exists_on_server(self):
        conf = self.create_upload_conf(self.obj, obj_exists=True)
        result = self.obj.upload(conf)
        self.assertEqual(result, ObjectUploadResult.EXISTS)

    def test_does_not_upload_chunk_when_it_exists_on_server(self):
        conf = self.create_upload_conf(self.obj, chunk_exists=True)
        result = self.obj.upload(conf)
        self.assertEqual(len(self.httpd.requests), 0)
        self.assertEqual(result, ObjectUploadResult.SUCCESS)

    def test_upload_returns_fail_when_chunk_upload_fails(self):
        conf = self.create_upload_conf(self.obj, success=False)
        result = self.obj.upload(conf)
        self.assertEqual(result, ObjectUploadResult.FAIL)

    def test_upload_requests_payload_are_made_correctly(self):
        conf = self.create_upload_conf(self.obj)
        self.obj.upload(conf)
        self.assertEqual(len(self.httpd.requests), 4)
        self.assertEqual(self.httpd.requests[0].body, b's')
        self.assertEqual(self.httpd.requests[1].body, b'p')
        self.assertEqual(self.httpd.requests[2].body, b'a')
        self.assertEqual(self.httpd.requests[3].body, b'm')
