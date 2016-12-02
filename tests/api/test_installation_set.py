# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu.core.object import Object
from efu.core.installation_set import InstallationSet


class InstallationSetTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = Object(__file__, 'raw', {'target-device': '/'})

    def test_can_add_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        index = installation_set.add(self.obj)
        self.assertEqual(index, 0)
        self.assertEqual(len(installation_set), 1)
        obj = installation_set.get(index)
        self.assertEqual(obj, self.obj)

    def test_can_get_object_by_index(self):
        installation_set = InstallationSet()
        installation_set.add(self.obj)
        obj = installation_set.get(0)
        self.assertEqual(obj, self.obj)

    def test_get_object_raises_error_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.get(100)

    def test_can_update_object(self):
        installation_set = InstallationSet()
        index = installation_set.add(self.obj)
        obj = installation_set.get(index)
        self.assertEqual(obj.options['target-device'], '/')
        installation_set.update(index, 'target-device', '/dev/sda')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_update_object_raises_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.update(100, 'target-device', '/dev/sda')

    def test_can_remove_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        index = installation_set.add(self.obj)
        self.assertEqual(len(installation_set), 1)
        installation_set.remove(index)
        self.assertEqual(len(installation_set), 0)

    def test_remove_object_raises_error_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.remove(100)

    def test_installation_set_as_metadata(self):
        installation_set = InstallationSet()
        installation_set.add(self.obj)
        metadata = installation_set.metadata()
        self.assertEqual(len(metadata), 1)
        # First object metadata
        self.assertEqual(metadata[0], self.obj.metadata())

    def test_installation_set_as_template(self):
        installation_set = InstallationSet()
        installation_set.add(self.obj)
        template = installation_set.template()
        self.assertEqual(len(template), 1)
        # First object template
        self.assertEqual(template[0], self.obj.template())

    def test_installation_set_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/installation_set')
        self.addCleanup(os.chdir, cwd)
        with open('set.txt') as fp:
            expected = fp.read()
        installation_set = InstallationSet()
        for _ in range(3):
            installation_set.add(Object(
                'set.txt', 'raw', {'target-device': '/dev/sda'}))
        observed = str(installation_set)
        self.assertEqual(observed, expected)
