# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.core import exceptions, Object, Chunk

from ..base import ObjectMockMixin, BaseTestCase


class ChunkTestCase(ObjectMockMixin, BaseTestCase):

    def test_empty_chunk_returns_None(self):
        self.assertIsNone(Chunk(b'', 1))
        self.assertIsNotNone(Chunk(b'0', 1))

    def test_chunk_sha256sum(self):
        chunk = Chunk(b'spam', 1)
        expected = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        observed = chunk.sha256sum
        self.assertEqual(observed, expected)

    def test_chunk_number(self):
        chunk = Chunk(b'spam', 10)
        self.assertEqual(chunk.number, 10)

    def test_chunk_as_dict(self):
        expected = {
            'number': 0,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        }
        observed = Chunk(b'spam', 0).as_dict()
        self.assertEqual(observed, expected)


class ObjectTestCase(ObjectMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.filename = self.create_file(b'spam')
        self.spam_sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        self.options = {
            'install-mode': 'raw',
            'target-device': 'device'
        }

    def test_object_validation(self):
        with self.assertRaises(exceptions.InvalidObjectError):
            Object('inexistent_file.bin', self.options)

    def test_object_sha256sum(self):
        obj = Object(self.filename, self.options)
        expected = self.spam_sha256sum
        observed = obj.sha256sum
        self.assertEqual(observed, expected)

    def test_object_n_chunks(self):
        obj = Object(self.filename, self.options)
        self.assertEqual(obj.n_chunks, 4)

    def test_object_as_dict(self):
        obj = Object(self.filename, self.options)
        expected = {
            'id': self.filename,
            'sha256sum': self.spam_sha256sum,
            'parts': [
                Chunk(b's', 0).as_dict(),
                Chunk(b'p', 1).as_dict(),
                Chunk(b'a', 2).as_dict(),
                Chunk(b'm', 3).as_dict()
            ],
            'metadata': {
                'filename': obj.filename,
                'sha256sum': self.spam_sha256sum,
                'size': 4,
                'install-mode': 'raw',
                'target-device': 'device',
            }
        }
        observed = obj.as_dict()
        self.assertEqual(observed, expected)

    def test_object_metadata(self):
        obj = Object(self.filename, self.options)
        expected = {
            'filename': obj.filename,
            'sha256sum': self.spam_sha256sum,
            'size': 4,
            'install-mode': 'raw',
            'target-device': 'device',
        }
        observed = obj.metadata
        self.assertEqual(observed, expected)

    def test_filename(self):
        fn = __file__
        obj = Object(fn, self.options)
        self.assertEqual(obj.filename, fn)

    def test_object_size(self):
        obj = Object(self.filename, self.options)
        expected = 4
        observed = obj.size
        self.assertEqual(observed, expected)

    def test_chunk_numbers(self):
        obj = Object(self.filename, self.options)
        expected = [0, 1, 2, 3]
        observed = [chunk.number for chunk in obj.chunks]
        self.assertEqual(observed, expected)

    def test_read_object(self):
        obj = Object(self.filename, self.options)
        obj._fd.seek(0)
        self.assertEqual(obj._read().data, b's')
        self.assertEqual(obj._read().data, b'p')
        self.assertEqual(obj._read().data, b'a')
        self.assertEqual(obj._read().data, b'm')
        self.assertIsNone(obj._read())
