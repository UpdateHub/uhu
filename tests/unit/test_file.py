# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib

from efu.push import exceptions
from efu.push.file import File

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
