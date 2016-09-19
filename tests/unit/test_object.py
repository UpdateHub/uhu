# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from unittest.mock import patch

from efu.core import Object, Chunk
from efu.core.object import hashlib

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

    def test_chunk_serialized(self):
        expected = {
            'number': 0,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        }
        observed = Chunk(b'spam', 0).serialize()
        self.assertEqual(observed, expected)


class ObjectTestCase(ObjectMockMixin, BaseTestCase):

    def setUp(self):
        super().setUp()
        self.content = b'spam'
        self.content_sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        self.filename = self.create_file(self.content)
        self.options = {
            'mode': 'raw',
            'target-device': 'device'
        }

    def test_object_filename(self):
        obj = Object(__file__, self.options)
        self.assertEqual(obj.filename, __file__)

    def test_object_sha256sum_is_none_when_not_loaded(self):
        obj = Object(self.filename, self.options)
        self.assertIsNone(obj.sha256sum)

    def test_loaded_object_sha256sum(self):
        obj = Object(self.filename, self.options)
        expected = self.content_sha256sum
        obj.load()
        observed = obj.sha256sum
        self.assertEqual(observed, expected)

    def test_object_n_chunks_is_none_when_not_loaded(self):
        obj = Object(self.filename, self.options)
        self.assertIsNone(obj.n_chunks)

    def test_loaded_object_n_chunks(self):
        obj = Object(self.filename, self.options)
        obj.load()
        self.assertEqual(obj.n_chunks, 4)

    def test_object_size_is_none_when_object_is_not_loaded(self):
        obj = Object(self.filename, self.options)
        self.assertIsNone(obj.size)

    def test_loaded_object_size(self):
        obj = Object(self.filename, self.options)
        obj.load()
        self.assertEqual(obj.size, 4)

    def test_read_object(self):
        obj = Object(self.filename, self.options)
        obj._fd.seek(0)
        self.assertEqual(obj._read().data, b's')
        self.assertEqual(obj._read().data, b'p')
        self.assertEqual(obj._read().data, b'a')
        self.assertEqual(obj._read().data, b'm')
        self.assertIsNone(obj._read())

    def test_object_metadata(self):
        obj = Object(self.filename, self.options)
        obj.load()
        self.assertEqual(obj.metadata.size, 4)
        self.assertEqual(obj.metadata.filename, obj.filename)
        self.assertEqual(obj.metadata.sha256sum, obj.sha256sum)
        self.assertEqual(obj.metadata.mode, 'raw')
        self.assertEqual(obj.metadata.target_device, 'device')

    def test_serialized_object(self):
        obj = Object(self.filename, self.options)
        expected = {
            'id': self.filename,
            'sha256sum': self.content_sha256sum,
            'parts': [
                Chunk(b's', 0).serialize(),
                Chunk(b'p', 1).serialize(),
                Chunk(b'a', 2).serialize(),
                Chunk(b'm', 3).serialize()
            ],
            'metadata': {
                'filename': obj.filename,
                'sha256sum': self.content_sha256sum,
                'size': 4,
                'mode': 'raw',
                'target-device': 'device',
            }
        }
        observed = obj.serialize()
        self.assertEqual(observed, expected)

    def test_does_not_load_object_twice(self):
        obj = Object(self.filename, self.options)
        self.assertFalse(obj._loaded)
        obj.load()
        with patch('hashlib.sha256') as mock:
            obj.load()
            self.assertFalse(mock.called)
