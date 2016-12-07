# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu.core.object import Object


class CompressedObjectTestCase(unittest.TestCase):

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.fixtures_dir = os.path.join(base_dir, '../fixtures/compressed/')
        uncompressed_fn = os.path.join(self.fixtures_dir, 'base.txt')
        self.size = os.path.getsize(uncompressed_fn)

    def test_can_get_gzip_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.get_uncompressed_size(), self.size)

    def test_can_get_lzma_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.xz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.get_uncompressed_size(), self.size)

    def test_can_get_lzo_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.get_uncompressed_size(), self.size)

    def test_can_get_tar_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        expected = os.path.getsize(
            os.path.join(self.fixtures_dir, 'archive.tar'))
        self.assertEqual(obj.get_uncompressed_size(), expected)

    def test_uncompressed_size_of_uncompressed_object_is_None(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertIsNone(obj.get_uncompressed_size())

    def test_can_work_with_symbolic_links(self):
        fn = os.path.join(self.fixtures_dir, 'symbolic.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.get_uncompressed_size(), self.size)

    def test_can_represent_compressed_object_as_metadata(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        metadata = obj.metadata()
        self.assertTrue(metadata['compressed'])
        self.assertEqual(metadata['required-uncompressed-size'], self.size)

    def test_can_represent_compressed_object_of_symlink_as_metadata(self):
        fn = os.path.join(self.fixtures_dir, 'symbolic.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        metadata = obj.metadata()
        self.assertTrue(metadata['compressed'])
        self.assertEqual(metadata['required-uncompressed-size'], self.size)

    def test_cannot_overwrite_compression_properties_on_metadata(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.bz2')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        obj._compressed = True  # it's a compressed file, but not supported
        obj.compressor = 'gzip'  # and it is a bz2, not a gzip.
        metadata = obj.metadata()  # luckily metadata will ignore all this
        self.assertIsNone(metadata.get('compressed'))
        self.assertIsNone(metadata.get('required-uncompressed-size'))

    def test_updating_filename_cleans_compression(self):
        uncompressed_fn = os.path.join(self.fixtures_dir, 'base.txt')
        compressed_fn = os.path.join(self.fixtures_dir, 'base.txt.gz')

        obj = Object(uncompressed_fn, 'raw', {'target-device': '/'})
        metadata = obj.metadata()
        self.assertIsNone(metadata.get('compressed'))

        obj.update('filename', compressed_fn)
        metadata = obj.metadata()
        self.assertEqual(metadata['compressed'], True)

        obj.update('filename', uncompressed_fn)
        metadata = obj.metadata()
        self.assertIsNone(metadata.get('compressed'))
