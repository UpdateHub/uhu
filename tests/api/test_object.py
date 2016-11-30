# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import unittest

from efu.core import Object
from efu.utils import CHUNK_SIZE_VAR

from utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


class ObjectTestCase(EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def test_can_create_object(self):
        fn = __file__
        mode = 'raw'
        options = {'target-device': '/dev/sda'}
        obj = Object(fn, mode, options)
        self.assertEqual(obj.filename, fn)
        self.assertEqual(obj.mode, mode)
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_can_get_object_size(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        fn = self.create_file(b'0' * 10)
        obj = Object(fn, 'raw', {'target-device': '/dev/sda'})
        obj.load()
        self.assertEqual(len(obj), 5)

    def test_object_size_raises_error_if_not_loaded(self):
        fn = self.create_file(b'0' * 10)
        obj = Object(fn, 'raw', {'target-device': '/dev/sda'})
        with self.assertRaises(RuntimeError):
            len(obj)

    def test_can_update_object(self):
        obj = Object(__file__, 'raw', {'target-device': '/dev/sda'})
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        obj.update('target-device', '/dev/sdb')
        self.assertEqual(obj.options['target-device'], '/dev/sdb')

    def test_update_object_raises_error_if_invalid_option(self):
        obj = Object(__file__, 'raw', {'target-device': '/dev/sda'})
        with self.assertRaises(ValueError):
            obj.update('target-path', '/')  # invalid in raw mode
        self.assertIsNone(obj.options.get('target-path'))

    def test_can_update_object_filename(self):
        obj = Object(__file__, 'raw', {'target-device': '/dev/sda'})
        self.assertEqual(obj.filename, __file__)
        obj.update('filename', 'new-filename')
        self.assertEqual(obj.filename, 'new-filename')

    def test_update_object_filename_raises_error_if_invalid_filename(self):
        obj = Object(__file__, 'raw', {'target-device': '/dev/sda'})
        with self.assertRaises(ValueError):
            obj.update('filename', '')  # empty string is invalid
        self.assertEqual(obj.filename, __file__)

    def test_object_raises_error_if_invalid_filename(self):
        with self.assertRaises(ValueError):
            Object('', 'raw', {'target-device': '/'})
        with self.assertRaises(TypeError):
            Object(lambda: 'bad filename type', 'raw', {'target-device': '/'})


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
        obj = Object(self.fn, mode, options)

        self.assertIsNone(obj.size)
        self.assertIsNone(obj.sha256sum)
        obj.load()
        self.assertEqual(obj.size, 4)
        self.assertEqual(obj.sha256sum, sha256sum)


class ObjectStringRepresentationTestCase(unittest.TestCase):

    def setUp(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/object')
        self.addCleanup(os.chdir, cwd)

    def get_fixture(self, fn):
        with open(fn) as fp:
            return fp.read().strip()

    def test_copy_default(self):
        expected = self.get_fixture('copy_default.txt')
        options = {
            'target-device': '/dev/sda',
            'target-path': '/',
            'filesystem': 'ext4',
        }
        obj = Object('copy_full.txt', mode='copy', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_copy_full_string(self):
        expected = self.get_fixture('copy_full.txt')
        options = {
            'target-device': '/dev/sda',
            'target-path': '/',
            'filesystem': 'ext4',
            'mount-options': '--all',
            'format?': True,
            'format-options': '-b 1024',
        }
        obj = Object('copy_full.txt', mode='copy', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_raw_default(self):
        expected = self.get_fixture('raw_default.txt')
        options = {'target-device': '/dev/sda'}
        obj = Object('raw_full.txt', mode='raw', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_raw_full_string(self):
        expected = self.get_fixture('raw_full.txt')
        options = {
            'target-device': '/dev/sda',
            'truncate': True,
            'seek': 10,
            'skip': 20,
            'count': 30,
            'chunk-size': 4096,
        }
        obj = Object('raw_full.txt', mode='raw', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_tarball_default(self):
        expected = self.get_fixture('tarball_default.txt')
        options = {
            'target-device': '/dev/sda',
            'target-path': '/',
            'filesystem': 'ext4',
        }
        obj = Object('tarball_full.txt', mode='tarball', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_tarball_full_string(self):
        expected = self.get_fixture('tarball_full.txt')
        options = {
            'target-device': '/dev/sda',
            'target-path': '/',
            'filesystem': 'ext4',
            'mount-options': '--all',
            'format?': True,
            'format-options': '-b 1024',
        }
        obj = Object('tarball_full.txt', mode='tarball', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)


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
        obj = Object(self.fn, 'raw', {'target-device': '/dev/sda'})
        obj.load()
        metadata = obj.metadata()
        self.assertEqual(metadata['mode'], 'raw')
        self.assertEqual(metadata['filename'], self.fn)
        self.assertEqual(metadata['target-device'], '/dev/sda')
        self.assertEqual(metadata['sha256sum'], self.sha256sum)
        self.assertEqual(metadata['size'], 4)

    def test_can_serialize_as_template(self):
        obj = Object(self.fn, 'raw', {'target-device': '/dev/sda'})
        template = obj.template()
        self.assertEqual(len(template), 4)
        self.assertEqual(template['filename'], self.fn)
        self.assertEqual(template['mode'], 'raw')
        self.assertFalse(template['compressed'])
        options = template['options']
        self.assertEqual(len(options), 7)
        self.assertEqual(options['target-device'], '/dev/sda')
        self.assertFalse(options['truncate'])
        self.assertEqual(options['seek'], 0)
        self.assertEqual(options['skip'], 0)
        self.assertEqual(options['count'], -1)
        self.assertEqual(options['chunk-size'], 131072)
        self.assertEqual(options['install-condition'], 'always')

    def test_template_serializations_keeps_equal_after_object_load(self):
        obj = Object(self.fn, 'raw', {'target-device': '/dev/sda'})
        expected = obj.template()
        obj.load()
        observed = obj.template()
        self.assertEqual(expected, observed)


class CompressedObjectTestCase(unittest.TestCase):

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.fixtures_dir = os.path.join(base_dir, '../fixtures/compressed/')
        uncompressed_fn = os.path.join(self.fixtures_dir, 'base.txt')
        self.size = os.path.getsize(uncompressed_fn)

    def test_can_get_gzip_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_get_lzma_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.xz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_get_lzo_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

    def test_can_get_tar_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        expected = os.path.getsize(
            os.path.join(self.fixtures_dir, 'archive.tar'))
        self.assertEqual(obj.uncompressed_size, expected)

    def test_uncompressed_size_of_uncompressed_object_is_None(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertIsNone(obj.uncompressed_size)

    def test_can_work_with_symbolic_links(self):
        fn = os.path.join(self.fixtures_dir, 'symbolic.gz')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        self.assertEqual(obj.uncompressed_size, self.size)

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

    def test_metadata_raises_error_if_invalid_uncompressed_object(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.bz2')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        obj._compressed = True
        obj.compressor = 'gzip'
        with self.assertRaises(ValueError):
            obj.metadata()

    def test_can_represent_compressed_object_as_template(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        obj = Object(fn, mode='raw', options={'target-device': '/'})
        template = obj.template()
        self.assertTrue(template['compressed'])
        self.assertIsNone(template.get('required-uncompressed-size'))
