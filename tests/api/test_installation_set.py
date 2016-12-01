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

    def test_can_create_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        obj = installation_set.create(self.fn, self.mode, self.options)
        self.assertEqual(len(installation_set), 1)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj.options, self.options)

    def test_can_get_object_by_index(self):
        installation_set = InstallationSet()
        installation_set.create(self.fn, self.mode, self.options)
        obj = installation_set.get(0)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj.options, self.options)

    def test_get_object_raises_error_if_object_doesnt_exist(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.get(100)

    def test_can_update_object(self):
        installation_set = InstallationSet()
        obj = installation_set.create(self.fn, self.mode, self.options)
        self.assertEqual(obj.options['target-device'], '/')
        installation_set.update(0, 'target-device', '/dev/sda')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_update_object_raises_error_if_object_doesnt_exist(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.update(100, 'target-device', '/dev/sda')

    def test_can_remove_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        installation_set.create(self.fn, self.mode, self.options)
        self.assertEqual(len(installation_set), 1)
        installation_set.remove(0)
        self.assertEqual(len(installation_set), 0)

    def test_remove_object_raises_error_if_object_doesnt_exist(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.remove(100)

    def test_installation_set_as_metadata(self):
        installation_set = InstallationSet()
        obj = installation_set.create(self.fn, self.mode, self.options)
        metadata = installation_set.metadata()
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0], obj.metadata())

    def test_installation_set_as_template(self):
        installation_set = InstallationSet()
        obj = installation_set.create(self.fn, self.mode, self.options)
        template = installation_set.template()
        self.assertEqual(len(template), 1)
        self.assertEqual(template[0], obj.template())

    def test_installation_set_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/installation_set')
        self.addCleanup(os.chdir, cwd)
        with open('set.txt') as fp:
            expected = fp.read()
        installation_set = InstallationSet()
        for _ in range(3):
            installation_set.create(
                'set.txt', 'raw', {'target-device': '/dev/sda'})
        observed = str(installation_set)
        self.assertEqual(observed, expected)
