# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import unittest

from efu.core import Object
from efu.core.object import ObjectList, ObjectManager
from efu.utils import CHUNK_SIZE_VAR

from ..utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


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
        obj = Object(
            'copy_full.txt', mode='copy', options=options)
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
        obj = Object(
            'copy_full.txt', mode='copy', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_raw_default(self):
        expected = self.get_fixture('raw_default.txt')
        options = {'target-device': '/dev/sda'}
        obj = Object(
            'raw_full.txt', mode='raw', options=options)
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
        obj = Object(
            'raw_full.txt', mode='raw', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_tarball_default(self):
        expected = self.get_fixture('tarball_default.txt')
        options = {
            'target-device': '/dev/sda',
            'target-path': '/',
            'filesystem': 'ext4',
        }
        obj = Object(
            'tarball_full.txt', mode='tarball', options=options)
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
        obj = Object(
            'tarball_full.txt', mode='tarball', options=options)
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

    def test_can_represent_compressed_object_as_metadata(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
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


class ObjectListTestCase(unittest.TestCase):

    def setUp(self):
        self.fn = __file__
        self.mode = 'raw'
        self.options = {'target-device': '/'}

    def test_can_add_object(self):
        objects = ObjectList()
        self.assertEqual(len(objects), 0)
        obj = objects.add(self.fn, self.mode, self.options)
        self.assertEqual(len(objects), 1)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj.options, self.options)

    def test_can_get_object_by_index(self):
        objects = ObjectList()
        objects.add(self.fn, self.mode, self.options)
        obj = objects.get(0)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj.options, self.options)

    def test_get_object_raises_error_if_object_doesnt_exist(self):
        objects = ObjectList()
        with self.assertRaises(ValueError):
            objects.get(100)

    def test_can_update_object(self):
        objects = ObjectList()
        obj = objects.add(self.fn, self.mode, self.options)
        self.assertEqual(obj.options['target-device'], '/')
        objects.update(0, 'target-device', '/dev/sda')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_update_object_raises_error_if_object_doesnt_exist(self):
        objects = ObjectList()
        with self.assertRaises(ValueError):
            objects.update(100, 'target-device', '/dev/sda')

    def test_can_remove_object(self):
        objects = ObjectList()
        self.assertEqual(len(objects), 0)
        objects.add(self.fn, self.mode, self.options)
        self.assertEqual(len(objects), 1)
        objects.remove(0)
        self.assertEqual(len(objects), 0)

    def test_remove_object_raises_error_if_object_doesnt_exist(self):
        objects = ObjectList()
        with self.assertRaises(ValueError):
            objects.remove(100)

    def test_object_list_as_metadata(self):
        objects = ObjectList()
        obj = objects.add(self.fn, self.mode, self.options)
        metadata = objects.metadata()
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0], obj.metadata())

    def test_object_list_as_template(self):
        objects = ObjectList()
        obj = objects.add(self.fn, self.mode, self.options)
        template = objects.template()
        self.assertEqual(len(template), 1)
        self.assertEqual(template[0], obj.template())

    def test_object_list_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/object')
        self.addCleanup(os.chdir, cwd)
        with open('object_list.txt') as fp:
            expected = fp.read()
        objects = ObjectList()
        for _ in range(3):
            objects.add(
                'object_list.txt', 'raw', {'target-device': '/dev/sda'})
        observed = str(objects)
        self.assertEqual(observed, expected)


class ObjectManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.manager = ObjectManager()
        self.objects0 = self.manager.add_list()
        self.objects1 = self.manager.add_list()
        self.obj0 = self.manager.add(
            0, __file__, 'raw', {'target-device': '/dev/sda'})
        self.obj1 = self.manager.add(
            1, __file__, 'raw', {'target-device': '/dev/sdb'})

    def test_object_list_as_metadata(self):
        metadata = self.manager.metadata()
        self.assertEqual(len(metadata), 2)
        self.assertEqual(metadata[0], self.objects0.metadata())
        self.assertEqual(metadata[1], self.objects1.metadata())

    def test_object_list_as_template(self):
        template = self.manager.template()
        self.assertEqual(len(template), 2)
        self.assertEqual(template[0], self.objects0.template())
        self.assertEqual(template[1], self.objects1.template())

    def test_can_get_all_objects(self):
        objects = list(self.manager.all())
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0], self.obj0)
        self.assertEqual(objects[1], self.obj1)


class ObjectManagerListManagementTestCase(unittest.TestCase):

    def test_can_add_list(self):
        manager = ObjectManager()
        self.assertEqual(len(manager), 0)
        manager.add_list()
        self.assertIsInstance(manager.get_list(0), ObjectList)
        self.assertEqual(len(manager), 1)

    def test_can_get_list(self):
        manager = ObjectManager()
        expected = manager.add_list()
        observed = manager.get_list(0)
        self.assertEqual(observed, expected)

    def test_get_list_raises_error_if_list_does_not_exist(self):
        manager = ObjectManager()
        with self.assertRaises(ValueError):
            manager.get_list(100)

    def test_can_remove_list(self):
        manager = ObjectManager()
        manager.add_list()
        self.assertEqual(len(manager), 1)
        manager.remove_list(0)
        self.assertEqual(len(manager), 0)

    def test_remove_list_raises_error_if_list_does_not_exist(self):
        manager = ObjectManager()
        with self.assertRaises(ValueError):
            manager.remove_list(100)


class ObjectManagerObjectManagementTestCase(unittest.TestCase):

    def setUp(self):
        self.manager = ObjectManager()
        self.objects = self.manager.add_list()
        self.index = 0

    def test_can_add_object(self):
        self.assertEqual(len(self.objects), 0)
        obj = self.manager.add(
            self.index, __file__, mode='raw',
            options={'target-device': '/dev/sda'})
        self.assertEqual(len(self.objects), 1)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_can_get_object(self):
        expected = self.manager.add(
            self.index, __file__, mode='raw',
            options={'target-device': '/dev/sda'})
        observed = self.manager.get(self.index, 0)
        self.assertEqual(observed, expected)
        self.assertEqual(observed.filename, __file__)
        self.assertEqual(observed.mode, 'raw')
        self.assertEqual(observed.options['target-device'], '/dev/sda')

    def test_can_update_object(self):
        obj = self.manager.add(
            self.index, __file__, mode='raw',
            options={'target-device': '/dev/sda'})
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.manager.update(self.index, 0, 'target-device', '/dev/sdb')
        self.assertEqual(obj.options['target-device'], '/dev/sdb')

    def test_can_remove_object(self):
        self.manager.add(
            self.index, __file__, mode='raw',
            options={'target-device': '/dev/sda'})
        self.assertEqual(len(self.objects), 1)
        self.manager.remove(self.index, 0)
        self.assertEqual(len(self.objects), 0)

    def test_object_manager_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/object')
        self.addCleanup(os.chdir, cwd)

        manager = ObjectManager()
        args = ['object_manager.txt', 'raw', {'target-device': '/dev/sda'}]
        for i in range(2):
            manager.add_list()
            for _ in range(2):
                manager.add(i, *args)
        with open('object_manager.txt') as fp:
            expected = fp.read()
        observed = str(manager)
        self.assertEqual(observed, expected)
