# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.push import exceptions
from efu.push.file import File, FileChunk

from ..base import EFUTestCase


class FileChunkTestCase(EFUTestCase):

    def setUp(self):
        self.addCleanup(FileChunk.reset_number_generator)

    def test_number_generation(self):
        c1 = FileChunk(b'')
        c2 = FileChunk(b'')
        c3 = FileChunk(b'')
        self.assertEqual(c1.number, 0)
        self.assertEqual(c2.number, 1)
        self.assertEqual(c3.number, 2)

    def test_number_generator_reset(self):
        FileChunk(b'')
        FileChunk(b'')
        FileChunk.reset_number_generator()
        chunk = FileChunk(b'')
        self.assertEqual(chunk.number, 0)

    def test_chunk_sha256sum(self):
        c1 = FileChunk(b'spam')
        expected = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        observed = c1.sha256sum
        self.assertEqual(observed, expected)

    def test_chunk_as_dict(self):
        expected = {
            'number': 0,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        }
        observed = FileChunk(b'spam').as_dict()
        self.assertEqual(observed, expected)


class FileTestCase(EFUTestCase):

    def setUp(self):
        super().setUp()
        self.file_name = self.create_file(b'spam')
        self.spam_sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8

    def test_id_generation(self):
        f1 = File(self.file_name)
        f2 = File(self.file_name)
        f3 = File(self.file_name)
        self.assertEqual(f1.id, 0)
        self.assertEqual(f2.id, 1)
        self.assertEqual(f3.id, 2)

    def test_id_generator_reset(self):
        File(self.file_name)
        File(self.file_name)
        File._File__reset_id_generator()
        file = File(self.file_name)
        self.assertEqual(file.id, 0)

    def test_file_validation(self):
        with self.assertRaises(exceptions.InvalidFileError):
            File('inexistent_file.bin')

    def test_file_sha256sum(self):
        file = File(self.file_name)
        expected = self.spam_sha256sum
        observed = file.sha256sum
        self.assertEqual(observed, expected)

    def test_file_n_chunks(self):
        file = File(self.file_name)
        self.assertEqual(file.n_chunks, 4)

    def test_file_as_dict(self):
        file = File(self.file_name)
        expected = {
            'id': 0,
            'sha256sum': self.spam_sha256sum,
            'parts': [
                FileChunk(b's').as_dict(),
                FileChunk(b'p').as_dict(),
                FileChunk(b'a').as_dict(),
                FileChunk(b'm').as_dict()
            ],
            'metadata': {
                'sha256sum': self.spam_sha256sum
            }
        }
        observed = file.as_dict()
        self.assertEqual(observed, expected)
