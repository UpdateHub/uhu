# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import unittest

from efu.core import Object
from efu.utils import CHUNK_SIZE_VAR


class ObjectTestCase(unittest.TestCase):

    def test_can_create_object(self):
        fn = __file__
        mode = 'raw'
        options = {'target-device': '/dev/sda'}
        obj = Object(1, fn, mode, options)
        self.assertEqual(obj.uid, 1)
        self.assertEqual(obj.filename, fn)
        self.assertEqual(obj.mode, mode)
        self.assertEqual(obj.options['target-device'], '/dev/sda')


class LoadObjectTestCase(unittest.TestCase):

    def setUp(self):
        os.environ[CHUNK_SIZE_VAR] = '2'
        self.fn = '/tmp/efu-object'
        self.addCleanup(os.remove, self.fn)
        self.addCleanup(os.environ.pop, CHUNK_SIZE_VAR)

    def test_can_load_object(self):
        content = b'spam'
        sha256sum = hashlib.sha256(content).hexdigest()
        with open(self.fn, 'bw') as fp:
            fp.write(content)

        mode = 'raw'
        options = {'target-device': '/dev/sda'}
        obj = Object(1, self.fn, mode, options)

        self.assertIsNone(obj.size)
        self.assertIsNone(obj.sha256sum)
        self.assertEqual(len(obj.chunks), 0)

        obj.load()

        self.assertEqual(obj.size, 4)
        self.assertEqual(obj.sha256sum, sha256sum)
        self.assertEqual(len(obj.chunks), 2)

    def test_object_loaded_chunks(self):
        content = b'spam'
        content_sha256sum = hashlib.sha256(content).hexdigest()
        with open(self.fn, 'bw') as fp:
            fp.write(content)
        mode = 'raw'
        options = {'target-device': '/dev/sda'}
        obj = Object(1, self.fn, mode, options)
        obj.load()

        expected = [
            {
                'position': 0,
                'sha256sum': hashlib.sha256(b'sp').hexdigest()
            },
            {
                'position': 1,
                'sha256sum': hashlib.sha256(b'am').hexdigest()
            },
        ]
        self.assertEqual(obj.chunks, expected)


class ObjectSerializationTestCase(unittest.TestCase):

    def setUp(self):
        os.environ[CHUNK_SIZE_VAR] = '2'
        self.fn = '/tmp/efu-object'
        self.content = b'spam'
        self.sha256sum = hashlib.sha256(self.content).hexdigest()

        with open(self.fn, 'bw') as fp:
            fp.write(self.content)

        self.addCleanup(os.remove, self.fn)
        self.addCleanup(os.environ.pop, CHUNK_SIZE_VAR)

    def test_can_serialize_object(self):
        obj = Object(1, self.fn, 'raw', {'target-device': '/dev/sda'})
        obj.load()
        serialized = obj.serialize()
        # ID
        self.assertEqual(serialized['id'], obj.uid)
        # metadata
        metadata = serialized['metadata']
        self.assertEqual(metadata['mode'], 'raw')
        self.assertEqual(metadata['filename'], self.fn)
        self.assertEqual(metadata['target-device'], '/dev/sda')
        self.assertEqual(metadata['sha256sum'], self.sha256sum)
        self.assertEqual(metadata['size'], 4)
        # chunks
        chunks = serialized['chunks']
        self.assertEqual(len(chunks), 2)
        for chunk in chunks:
            self.assertEqual(chunks.index(chunk), chunk['position'])
        chunks[0]['sha256sum'] = hashlib.sha256(b'sp').hexdigest()
        chunks[1]['sha256sum'] = hashlib.sha256(b'am').hexdigest()

    def test_can_serialize_object_as_metadata(self):
        obj = Object(1, self.fn, 'raw', {'target-device': '/dev/sda'})
        obj.load()
        metadata = obj.metadata()
        self.assertEqual(metadata['mode'], 'raw')
        self.assertEqual(metadata['filename'], self.fn)
        self.assertEqual(metadata['target-device'], '/dev/sda')
        self.assertEqual(metadata['sha256sum'], self.sha256sum)
        self.assertEqual(metadata['size'], 4)

    def test_can_serialize_as_template(self):
        obj = Object(1, self.fn, 'raw', {'target-device': '/dev/sda'})
        template = obj.template()
        self.assertEqual(len(template), 3)
        self.assertEqual(template['filename'], self.fn)
        self.assertEqual(template['mode'], 'raw')
        options = template['options']
        self.assertEqual(len(options), 7)
        self.assertEqual(options['target-device'], '/dev/sda')
        self.assertFalse(options['truncate'])
        self.assertEqual(options['seek'], 0)
        self.assertEqual(options['skip'], 0)
        self.assertEqual(options['count'], -1)
        self.assertEqual(options['chunk-size'], 131072)
        self.assertFalse(options['compressed'])
