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
        obj.load()
        self.assertEqual(obj.size, 4)
        self.assertEqual(obj.sha256sum, sha256sum)


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
        self.assertEqual(len(template), 4)
        self.assertEqual(template['filename'], self.fn)
        self.assertEqual(template['mode'], 'raw')
        self.assertFalse(template['compressed'])
        options = template['options']
        self.assertEqual(len(options), 6)
        self.assertEqual(options['target-device'], '/dev/sda')
        self.assertFalse(options['truncate'])
        self.assertEqual(options['seek'], 0)
        self.assertEqual(options['skip'], 0)
        self.assertEqual(options['count'], -1)
        self.assertEqual(options['chunk-size'], 131072)


class CompressedObjectTestCase(unittest.TestCase):

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.fixtures_dir = os.path.join(base_dir, '../fixtures/compressed/')
        uncompressed_fn = os.path.join(self.fixtures_dir, 'base.txt')
        self.size = os.path.getsize(uncompressed_fn)

    def test_can_get_gzip_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.gz')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_get_lzma_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.xz')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_get_lzo_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_get_tar_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar.gz')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        expected = os.path.getsize(
            os.path.join(self.fixtures_dir, 'archive.tar'))
        self.assertEqual(obj.uncompressed_size, expected)

    def test_can_load_compressed_object_correctly(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        obj.load()
        self.assertTrue(obj.compressed)
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_represent_compressed_object_as_metadata(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        metadata = obj.metadata()
        self.assertTrue(metadata['compressed'])
        self.assertEqual(metadata['required-uncompressed-size'], self.size)

    def test_can_represent_compressed_object_as_template(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        template = obj.template()
        self.assertTrue(template['compressed'])
        self.assertIsNone(template.get('required-uncompressed-size'))

    def test_uncompressed_size_of_uncompressed_object_is_None(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar')
        obj = Object(0, fn, mode='raw', options={'target-device': '/'})
        self.assertIsNone(obj.uncompressed_size)
