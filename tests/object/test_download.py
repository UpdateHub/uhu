# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import tempfile
import shutil

from efu.core.object import Object
from efu.exceptions import DownloadError
from efu.utils import SERVER_URL_VAR

from utils import (
    EFUTestCase, HTTPTestCaseMixin, FileFixtureMixin, EnvironmentFixtureMixin)


class ObjectDownloadTestCase(EnvironmentFixtureMixin, FileFixtureMixin,
                             HTTPTestCaseMixin, EFUTestCase):

    def setUp(self):
        wd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, wd)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(wd)

        self.product = '1324'

        # object
        self.uid = 1
        self.fn = 'image.bin'
        self.content = b'spam'
        self.sha256 = hashlib.sha256(self.content).hexdigest()
        self.obj = Object('raw', {
            'filename': self.fn,
            'target-type': 'device',
            'target': '/dev/sda'
        })
        self.addCleanup(self.remove_file, self.fn)

        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))
        # url to download object
        self.path = '/download'
        self.url = self.httpd.url(self.path)
        self.httpd.register_response(
            self.path, 'GET', body=self.content, status_code=200)

    def test_can_download_object(self):
        self.assertFalse(self.obj.exists)
        self.obj.download(self.url)
        self.assertTrue(self.obj.exists)

    def test_object_integrity_after_download(self):
        self.assertFalse(self.obj.exists)
        self.obj.download(self.url)
        with open(self.fn, 'rb') as fp:
            observed = hashlib.sha256(fp.read()).hexdigest()
        self.assertEqual(observed, self.sha256)

    def test_download_raises_error_if_cant_reach_server(self):
        with self.assertRaises(DownloadError):
            self.obj.download('http://easyfota-unreach.com')

    def test_download_raises_error_if_bad_response(self):
        self.httpd.register_response(
            self.path, 'GET', body='{}', status_code=500)
        with self.assertRaises(DownloadError):
            self.obj.download(self.url)

    def test_do_not_download_when_object_exists_locally(self):
        with open(self.fn, 'bw') as fp:
            fp.write(self.content)
        self.assertTrue(self.obj.exists)
        self.obj.download(self.url)
        self.assertEqual(len(self.httpd.requests), 0)
