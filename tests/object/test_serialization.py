# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import unittest

from efu.core.object import Object


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
        self.fn = '/tmp/efu-object'
        self.content = b'spam'
        self.sha256sum = hashlib.sha256(self.content).hexdigest()
        self.addCleanup(os.remove, self.fn)
        with open(self.fn, 'bw') as fp:
            fp.write(self.content)

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
