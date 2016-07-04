# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib

from efu.push import exceptions
from efu.push.file import File, UploadStatus

from ..base import BasePushTestCase


class FileTestCase(BasePushTestCase):

    def setUp(self):
        super().setUp()
        self.file_name = self.fixture.create_file(b'\0')

    def test_can_reset_file_id_generation(self):
        f1 = File(self.file_name)
        f2 = File(self.file_name)
        f3 = File(self.file_name)
        self.assertEqual((f1.id, f2.id, f3.id), (0, 1, 2))

        File._File__reset_id_generator()

        f4 = File(self.file_name)
        f5 = File(self.file_name)
        f6 = File(self.file_name)
        self.assertEqual((f4.id, f5.id, f6.id), (0, 1, 2))

    def test_file_validation(self):
        with self.assertRaises(exceptions.InvalidFileError):
            File('inexistent_file.bin')

    def test_file_sha256(self):
        content = b'0'
        sha256 = hashlib.sha256(content).hexdigest()
        with open(self.file_name, 'wb') as fp:
            fp.write(content)

        file = File(self.file_name)
        self.assertEqual(file.sha256, sha256)

    def test_file_id(self):
        file = File(self.file_name)
        self.assertEqual(file.id, 0)

        file = File(self.file_name)
        self.assertEqual(file.id, 1)

        file = File(self.file_name)
        self.assertEqual(file.id, 2)

    def test_does_not_upload_when_file_exists_in_server(self):
        file = File(self.file_name)
        file.exists_in_server = True
        result = file.upload()
        self.assertEqual(result, UploadStatus.EXISTS)

    def test_upload_requests_payload_are_made_correctly(self):
        fn, conf = self.fixture.set_file(1, 1, content=b'1234', chunk_size=1)

        file = File(fn)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1
        file.upload()

        self.assertEqual(len(self.httpd.requests), 5)
        self.assertEqual(self.httpd.requests[0].body, b'1')
        self.assertEqual(self.httpd.requests[1].body, b'2')
        self.assertEqual(self.httpd.requests[2].body, b'3')
        self.assertEqual(self.httpd.requests[3].body, b'4')
        self.assertEqual(self.httpd.requests[4].body, b'')

    def test_upload_returns_failure_result_when_part_upload_fails(self):
        fn, conf = self.fixture.set_file(1, 1, part_success=False)

        file = File(fn)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.PART_FAIL)

    def test_upload_returns_failure_when_finishing_upload_fails(self):
        _, conf = self.fixture.set_file(1, 1, finish_success=False)

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.FAIL)

    def test_returns_success_when_upload_is_successful(self):
        _, conf = self.fixture.set_file(1, 1)

        file = File(self.file_name)
        file.exists_in_server = False
        file.part_upload_urls = conf['urls']
        file.finish_upload_url = conf['finish_upload_url']
        file.chunk_size = 1

        result = file.upload()
        self.assertEqual(result, UploadStatus.SUCCESS)
