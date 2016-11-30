# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu.core.installation_set import InstallationSet


class InstallationSetTestCase(unittest.TestCase):

    def setUp(self):
        self.fn = __file__
        self.mode = 'raw'
        self.options = {'target-device': '/'}

    def test_can_add_object(self):
        objects = InstallationSet()
        self.assertEqual(len(objects), 0)
        obj = objects.add(self.fn, self.mode, self.options)
        self.assertEqual(len(objects), 1)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj.options, self.options)

    def test_can_get_object_by_index(self):
        objects = InstallationSet()
        objects.add(self.fn, self.mode, self.options)
        obj = objects.get(0)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj.options, self.options)

    def test_get_object_raises_error_if_object_doesnt_exist(self):
        objects = InstallationSet()
        with self.assertRaises(ValueError):
            objects.get(100)

    def test_can_update_object(self):
        objects = InstallationSet()
        obj = objects.add(self.fn, self.mode, self.options)
        self.assertEqual(obj.options['target-device'], '/')
        objects.update(0, 'target-device', '/dev/sda')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_update_object_raises_error_if_object_doesnt_exist(self):
        objects = InstallationSet()
        with self.assertRaises(ValueError):
            objects.update(100, 'target-device', '/dev/sda')

    def test_can_remove_object(self):
        objects = InstallationSet()
        self.assertEqual(len(objects), 0)
        objects.add(self.fn, self.mode, self.options)
        self.assertEqual(len(objects), 1)
        objects.remove(0)
        self.assertEqual(len(objects), 0)

    def test_remove_object_raises_error_if_object_doesnt_exist(self):
        objects = InstallationSet()
        with self.assertRaises(ValueError):
            objects.remove(100)

    def test_installation_set_as_metadata(self):
        objects = InstallationSet()
        obj = objects.add(self.fn, self.mode, self.options)
        metadata = objects.metadata()
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0], obj.metadata())

    def test_installation_set_as_template(self):
        objects = InstallationSet()
        obj = objects.add(self.fn, self.mode, self.options)
        template = objects.template()
        self.assertEqual(len(template), 1)
        self.assertEqual(template[0], obj.template())

    def test_installation_set_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/installation_set')
        self.addCleanup(os.chdir, cwd)
        with open('set.txt') as fp:
            expected = fp.read()
        objects = InstallationSet()
        for _ in range(3):
            objects.add('set.txt', 'raw', {'target-device': '/dev/sda'})
        observed = str(objects)
        self.assertEqual(observed, expected)
