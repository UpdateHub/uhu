# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest
from unittest.mock import patch

from uhu.core.updatehub import (
    finish_package, ObjectUploadResult, push_package,
    upload_metadata, upload_object, upload_objects)
from uhu.exceptions import UploadError


class PushPackageTestCase(unittest.TestCase):

    @patch('uhu.core.updatehub.upload_metadata', return_value='1')
    @patch('uhu.core.updatehub.upload_objects')
    @patch('uhu.core.updatehub.finish_package')
    def test_returns_uid_when_successful(self, m1, m2, m3):
        uid = push_package({}, [])
        self.assertEqual(uid, '1')


class UploadMetadataTestCase(unittest.TestCase):

    @patch('uhu.core.updatehub.validate_metadata')
    @patch('uhu.core.updatehub.http.post')
    def test_returns_package_uid_when_successful(self, http, mock):
        http.return_value.status_code = 201
        http.return_value.json.return_value = {'uid': '1234'}
        uid = upload_metadata({})
        self.assertEqual(uid, '1234')

    def test_raises_error_when_invalid_metadata(self):
        with self.assertRaises(UploadError):
            upload_metadata({})

    @patch('uhu.core.updatehub.validate_metadata')
    @patch('uhu.core.updatehub.http.post')
    def test_raises_error_when_unathorized(self, http, mock):
        http.return_value.status_code = 401
        with self.assertRaises(UploadError):
            upload_metadata({})

    @patch('uhu.core.updatehub.validate_metadata')
    @patch('uhu.core.updatehub.http')
    def test_raises_error_if_invalid_request(self, http, mock):
        http.post.return_value.status_code = 400
        http.format_server_error.return_value = 'error'
        with self.assertRaises(UploadError):
            upload_metadata({})


class UploadObjectTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = {
            'filename': __file__,
            'sha256sum': 'sha1234',
            'md5': 'md51234',
            'chunks': 10,
        }
        self.package_uid = '1234'

    @patch('uhu.core.updatehub.http.post')
    @patch('uhu.core.updatehub.http.put')
    def test_returns_SUCCESS_when_upload_fails(self, put, post):
        post.return_value.status_code = 201
        post.return_value.json.return_value = {
            'storage': 'dummy',
            'url': 'http://someplace',
        }
        put.return_value.ok = True
        result = upload_object(self.obj, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.SUCCESS)

    @patch('uhu.core.updatehub.http.post')
    def test_raises_error_when_cannot_get_upload_url(self, http):
        http.return_value.status_code = 400
        with self.assertRaises(UploadError):
            upload_object(self.obj, self.package_uid)

    @patch('uhu.core.updatehub.http.post')
    def test_returns_EXISTS_when_file_exists_on_server(self, http):
        http.return_value.status_code = 200
        result = upload_object(self.obj, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.EXISTS)

    @patch('uhu.core.updatehub.http.post')
    @patch('uhu.core.updatehub.http.put')
    def test_returns_FAIL_when_upload_fails(self, put, post):
        post.return_value.status_code = 201
        post.return_value.json.return_value = {
            'storage': 'dummy',
            'url': 'http://someplace',
        }
        put.return_value.ok = False
        result = upload_object(self.obj, self.package_uid)
        self.assertEqual(result, ObjectUploadResult.FAIL)


class UploadObjectsTestCase(unittest.TestCase):

    @patch('uhu.core.updatehub.upload_object')
    def test_returns_None_when_successful(self, mock):
        mock.return_value = ObjectUploadResult.SUCCESS
        self.assertIsNone(upload_objects('1234', [{}]))

    @patch('uhu.core.updatehub.upload_object')
    def test_returns_None_when_file_exists(self, mock):
        mock.return_value = ObjectUploadResult.EXISTS
        self.assertIsNone(upload_objects('1234', [{}]))

    @patch('uhu.core.updatehub.upload_object')
    def test_raises_error_when_some_upload_fails(self, mock):
        mock.side_effect = [
            ObjectUploadResult.SUCCESS,
            ObjectUploadResult.FAIL,
        ]
        with self.assertRaises(UploadError):
            upload_objects('1234', [{}, {}])


class FinishPackageTestCase(unittest.TestCase):

    @patch('uhu.core.updatehub.http.put')
    def test_returns_None_when_successful(self, http):
        http.return_value.status_code = 204
        self.assertIsNone(finish_package('1234'))

    @patch('uhu.core.updatehub.http.put')
    def test_raises_error_when_fail(self, http):
        http.return_value.status_code = 400
        with self.assertRaises(UploadError):
            finish_package('1234')
