# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.push.file import File
from efu.push.upload import Upload, UploadStatus

from ..base import EFUTestCase


class UploadTestCase(EFUTestCase):

    def setUp(self):
        super().setUp()
        self.file = File(self.create_file(b'\0'))

    def test_does_not_upload_when_file_exists_in_server(self):
        meta = self.create_upload_meta(self.file, file_exists=True)
        result = Upload(self.file, meta).upload()
        self.assertEqual(result, UploadStatus.EXISTS)

    def test_returns_success_when_upload_is_successful(self):
        meta = self.create_upload_meta(self.file)
        result = Upload(self.file, meta).upload()
        self.assertEqual(result, UploadStatus.SUCCESS)

    def test_upload_requests_payload_are_made_correctly(self):
        file = File(self.create_file(b'1234'))
        meta = self.create_upload_meta(file)

        Upload(file, meta).upload()

        self.assertEqual(len(self.httpd.requests), 4)
        self.assertEqual(self.httpd.requests[0].body, b'1')
        self.assertEqual(self.httpd.requests[1].body, b'2')
        self.assertEqual(self.httpd.requests[2].body, b'3')
        self.assertEqual(self.httpd.requests[3].body, b'4')

    def test_upload_returns_failure_result_when_part_upload_fails(self):
        meta = self.create_upload_meta(self.file, success=False)
        result = Upload(self.file, meta).upload()
        self.assertEqual(result, UploadStatus.FAIL)
