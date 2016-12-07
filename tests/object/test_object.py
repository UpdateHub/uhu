# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib

from efu.core.object import Object
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

    def test_can_get_object_length(self):
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

    def test_can_load_object(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        content = b'spam'
        fn = self.create_file(content)
        sha256sum = hashlib.sha256(content).hexdigest()
        obj = Object(fn, 'raw', {'target-device': '/dev/sda'})
        self.assertIsNone(obj.size)
        self.assertIsNone(obj.sha256sum)
        obj.load()
        self.assertEqual(obj.size, 4)
        self.assertEqual(obj.sha256sum, sha256sum)

    def test_can_load_object_from_cache(self):
        cache = {
            'size': 100,
            'md5': 'md5',
            'sha256sum': 'sha256sum',
            'version': '2.0',
        }
        fn = self.create_file(b'spam')
        obj = Object(fn, 'raw', {'target-device': '/dev/sda'})
        obj.load(cache=cache)
        self.assertEqual(obj.size, 100)
        self.assertEqual(obj.md5, 'md5')
        self.assertEqual(obj.sha256sum, 'sha256sum')
        self.assertEqual(obj.version, '2.0')
