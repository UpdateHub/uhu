# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os

from efu.core.object import Object
from efu.utils import CHUNK_SIZE_VAR

from utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


class ObjectTestCase(EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def setUp(self):
        super().setUp()
        self.options = {
            'filename': __file__,
            'target-type': 'device',
            'target': '/dev/sda',
        }

    def test_can_create_object(self):
        obj = Object('raw', self.options)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.size, os.path.getsize(__file__))
        self.assertEqual(obj['target-type'], 'device')
        self.assertEqual(obj['target'], '/dev/sda')

    def test_create_object_raises_error_if_unknow_mode(self):
        with self.assertRaises(ValueError):
            Object('unknow', {})

    def test_can_get_object_length(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        self.options['filename'] = self.create_file(b'0' * 10)
        obj = Object('raw', self.options)
        self.assertEqual(len(obj), 5)

    def test_can_iter_over_the_object_content(self):
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        self.options['filename'] = self.create_file(b'spam')
        obj = Object('raw', self.options)
        expected = [b's', b'p', b'a', b'm']
        observed = list(obj)
        self.assertEqual(expected, observed)

    def test_exists_return_True_if_file_do_exist(self):
        obj = Object('raw', self.options)
        self.assertEqual(obj.exists, True)

    def test_exists_return_False_if_file_does_not_exist(self):
        self.options['filename'] = 'doesnt-exist'
        obj = Object('raw', self.options)
        self.assertEqual(obj.exists, False)

    def test_can_load_object(self):
        content = b'spam'
        sha256sum = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()
        self.options['filename'] = self.create_file(content)
        obj = Object('raw', self.options)
        self.assertIsNone(obj.md5)
        self.assertIsNone(obj['sha256sum'])
        obj.load()
        self.assertEqual(obj.md5, md5)
        self.assertEqual(obj['sha256sum'], sha256sum)

    def test_can_generate_metadata(self):
        content = b'spam'
        fn = self.create_file(content)
        obj = Object('raw', {
            'filename': fn,
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
        })
        expected = {
            'mode': 'raw',
            'filename': fn,
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
            'size': len(content),
            'sha256sum': hashlib.sha256(content).hexdigest(),
        }
        self.assertEqual(obj.metadata(), expected)

    def test_can_generate_template(self):
        obj = Object('raw', {
            'filename': __file__,
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
        })
        expected = {
            'mode': 'raw',
            'filename': __file__,
            'install-condition': 'always',
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
        }
        self.assertEqual(obj.template(), expected)

    def test_can_update_object(self):
        obj = Object('raw', self.options)
        self.assertEqual(obj['target'], '/dev/sda')
        obj.update('target', '/dev/sdb')
        self.assertEqual(obj['target'], '/dev/sdb')

    def test_update_object_raises_error_if_invalid_option(self):
        obj = Object('raw', self.options)
        with self.assertRaises(ValueError):
            obj.update('target-path', '/')  # invalid in raw mode
        with self.assertRaises(ValueError):
            obj['target-path']
