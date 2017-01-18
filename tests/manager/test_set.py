# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu.core.object import Object
from efu.core.manager import InstallationSet


class InstallationSetTestCase(unittest.TestCase):

    def setUp(self):
        self.fn = __file__
        self.mode = 'raw'
        self.options = {
            'filename': __file__,
            'target-type': 'device',
            'target': '/dev/sda',
        }
        self.obj = Object(self.mode, self.options)

    def test_can_create_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        index = installation_set.create(self.mode, self.options)
        self.assertEqual(index, 0)
        self.assertEqual(len(installation_set), 1)
        obj = installation_set.get(index)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj['target'], '/dev/sda')

    def test_can_get_object_by_index(self):
        installation_set = InstallationSet()
        installation_set.create(self.mode, self.options)
        obj = installation_set.get(0)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj['target'], '/dev/sda')

    def test_get_object_raises_error_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.get(100)

    def test_can_update_object(self):
        installation_set = InstallationSet()
        index = installation_set.create(self.mode, self.options)
        obj = installation_set.get(index)
        self.assertEqual(obj['target'], '/dev/sda')
        installation_set.update(index, 'target', '/')
        self.assertEqual(obj['target'], '/')

    def test_update_object_raises_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.update(100, 'target', '/dev/sda')

    def test_can_remove_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        index = installation_set.create(self.mode, self.options)
        self.assertEqual(len(installation_set), 1)
        installation_set.remove(index)
        self.assertEqual(len(installation_set), 0)

    def test_remove_object_raises_error_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.remove(100)

    def test_installation_set_as_metadata(self):
        installation_set = InstallationSet()
        installation_set.create(self.mode, self.options)
        metadata = installation_set.metadata()
        self.assertEqual(len(metadata), 1)
        # First object metadata
        self.assertEqual(metadata[0], self.obj.metadata())

    def test_installation_set_as_template(self):
        installation_set = InstallationSet()
        installation_set.create(self.mode, self.options)
        template = installation_set.template()
        self.assertEqual(len(template), 1)
        # First object template
        self.assertEqual(template[0], self.obj.template())

    def test_installation_set_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/manager/fixtures')
        self.addCleanup(os.chdir, cwd)
        with open('set.txt') as fp:
            expected = fp.read()
        installation_set = InstallationSet()
        self.options['filename'] = 'set.txt'
        for _ in range(3):
            installation_set.create(self.mode, self.options)
        self.assertEqual(str(installation_set), expected)
