# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

from uhu.core.object import Object, ObjectUploadResult
from uhu.exceptions import UploadError
from uhu.utils import CHUNK_SIZE_VAR, SERVER_URL_VAR

from utils import (
    UHUTestCase, EnvironmentFixtureMixin, FileFixtureMixin,
    HTTPTestCaseMixin, UploadFixtureMixin)


class UploadTestCase(
        UploadFixtureMixin, EnvironmentFixtureMixin, FileFixtureMixin,
        HTTPTestCaseMixin, UHUTestCase):

    def setUp(self):
        super().setUp()
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        self.obj_fn = self.create_file(b'spam')
        self.options = {
            'filename': self.obj_fn,
            'target-type': 'device',
            'target': '/dev/sda'
        }
        self.obj = Object('raw', self.options)
        self.obj.load()
        self.product_uid = '0' * 64
        self.package_uid = '1' * 64

    def test_upload_returns_success_when_successful(self):
        self.create_upload_conf(self.obj, self.product_uid, self.package_uid)
        result = self.obj.upload(self.product_uid, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.SUCCESS)

    def test_upload_raises_error_when_cannot_start_upload(self):
        self.create_upload_conf(
            self.obj, self.product_uid, self.package_uid,
            start_success=False)
        with self.assertRaises(UploadError):
            self.obj.upload(self.product_uid, self.package_uid)

    def test_does_not_upload_when_file_exists_on_server(self):
        self.create_upload_conf(
            self.obj, self.product_uid, self.package_uid, exists=True)
        result = self.obj.upload(self.product_uid, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.EXISTS)

    def test_upload_returns_fail_when_upload_fails(self):
        self.create_upload_conf(
            self.obj, self.product_uid, self.package_uid,
            upload_success=False)
        result = self.obj.upload(self.product_uid, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.FAIL)

    def test_can_upload_compressed_object_from_symbolic_link(self):
        self.options['filename'] = 'tests/fixtures/compressed/symbolic.gz'
        obj = Object('raw', self.options)
        self.create_upload_conf(obj, self.product_uid, self.package_uid)
        result = obj.upload(self.product_uid, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.SUCCESS)
