# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest

from efu.core.installation_set import (
    InstallationSet, InstallationSetManager, InstallationSetMode)


class InstallationSetModeTestCase(unittest.TestCase):

    def test_can_return_mode_from_objects_set(self):
        single = InstallationSetMode.from_objects([[]])
        self.assertEqual(single, InstallationSetMode.Single)

        active_inactive = InstallationSetMode.from_objects([[], []])
        self.assertEqual(active_inactive, InstallationSetMode.ActiveInactive)

    def test_raises_error_if_objects_is_empty(self):
        with self.assertRaises(ValueError):
            InstallationSetMode.from_objects([])


class InstallationSetManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.manager = InstallationSetManager(
            InstallationSetMode.ActiveInactive)
        self.set0 = self.manager.get_set(0)
        self.set1 = self.manager.get_set(1)
        self.obj0 = self.manager.add(
            __file__, 'raw', {'target-device': '/dev/sda'}, index=0)
        self.obj1 = self.manager.add(
            __file__, 'raw', {'target-device': '/dev/sdb'}, index=1)

    def test_installation_set_as_metadata(self):
        metadata = self.manager.metadata()
        self.assertEqual(len(metadata), 2)
        self.assertEqual(metadata[0], self.set0.metadata())
        self.assertEqual(metadata[1], self.set1.metadata())

    def test_installation_set_as_template(self):
        template = self.manager.template()
        self.assertEqual(len(template), 2)
        self.assertEqual(template[0], self.set0.template())
        self.assertEqual(template[1], self.set1.template())

    def test_installation_set_manager_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/installation_set')
        self.addCleanup(os.chdir, cwd)

        manager = InstallationSetManager(InstallationSetMode.ActiveInactive)
        options = {'target-device': '/dev/sda'}
        args = ['manager.txt', 'raw', options]
        for i in range(2):
            manager.add(*args, index=i)
        with open('manager.txt') as fp:
            expected = fp.read()
        observed = str(manager)
        self.assertEqual(observed, expected)


class InstallationSetManagerSetManagementTestCase(unittest.TestCase):

    def test_is_single_returns_True_when_single(self):
        manager = InstallationSetManager(InstallationSetMode.Single)
        self.assertTrue(manager.is_single())

    def test_is_single_returns_False_when_not_single(self):
        manager = InstallationSetManager(InstallationSetMode.ActiveInactive)
        self.assertFalse(manager.is_single())

    def test_cannot_add_more_sets_than_allowed_by_mode(self):
        manager = InstallationSetManager(InstallationSetMode.Single)
        self.assertEqual(len(manager), 1)
        with self.assertRaises(ValueError):
            manager._add_set()

    def test_can_get_installation_set(self):
        manager = InstallationSetManager(InstallationSetMode.Single)
        set_ = manager.get_set(0)
        self.assertIsInstance(set_, InstallationSet)

    def test_get_set_raises_error_if_set_does_not_exist(self):
        manager = InstallationSetManager(InstallationSetMode.Single)
        with self.assertRaises(ValueError):
            manager.get_set(100)

    def test_get_set_returns_first_set_when_single_mode(self):
        manager = InstallationSetManager(InstallationSetMode.Single)
        set_ = manager.get_set()
        self.assertIsInstance(set_, InstallationSet)

    def test_get_set_raises_if_not_single_and_index_is_not_passed(self):
        manager = InstallationSetManager(InstallationSetMode.ActiveInactive)
        with self.assertRaises(TypeError):
            manager.get_set()


class SingleModeInstallationSetManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.manager = InstallationSetManager(InstallationSetMode.Single)
        self.installation_set = self.manager.get_set(0)

    def test_can_add_object(self):
        self.assertEqual(len(self.installation_set), 0)
        obj = self.manager.add(
            __file__, mode='raw', options={'target-device': '/dev/sda'})
        self.assertEqual(len(self.installation_set), 1)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_can_get_object(self):
        expected = self.manager.add(
            __file__, mode='raw', options={'target-device': '/dev/sda'})
        observed = self.manager.get(0)
        self.assertEqual(observed, expected)
        self.assertEqual(observed.filename, __file__)
        self.assertEqual(observed.mode, 'raw')
        self.assertEqual(observed.options['target-device'], '/dev/sda')

    def test_can_update_object(self):
        obj = self.manager.add(
            __file__, mode='raw', options={'target-device': '/dev/sda'})
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.manager.update(0, 'target-device', '/dev/sdb')
        self.assertEqual(obj.options['target-device'], '/dev/sdb')

    def test_can_remove_object(self):
        self.manager.add(
            __file__, mode='raw', options={'target-device': '/dev/sda'})
        self.assertEqual(len(self.installation_set), 1)
        self.manager.remove(0)
        self.assertEqual(len(self.installation_set), 0)

    def test_can_get_all_objects(self):
        expected = []
        for _ in range(2):
            expected.append(self.manager.add(
                __file__, mode='raw', options={'target-device': '/dev/sda'}))
        observed = list(self.manager.all())
        self.assertEqual(expected, observed)


class ActiveInactiveModeInstallationSetManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.manager = InstallationSetManager(
            InstallationSetMode.ActiveInactive)
        self.obj_fn = __file__
        self.obj_mode = 'raw'
        self.obj_options = {'target-device': '/dev/sda'}

    def test_can_add_object(self):
        for installation_set in self.manager:
            self.assertEqual(len(installation_set), 0)
        observed = []
        for i in range(2):
            observed.append(self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i))
        for installation_set in self.manager:
            self.assertEqual(len(installation_set), 1)
        for obj in observed:
            self.assertEqual(obj.filename, self.obj_fn)
            self.assertEqual(obj.mode, self.obj_mode)
            self.assertEqual(obj.options, self.obj_options)

    def test_add_object_raises_error_if_index_is_not_specified(self):
        with self.assertRaises(TypeError):
            self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options)

    def test_can_get_object(self):
        expected = []
        for i in range(2):
            expected.append(self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i))
        observed = []
        for i in range(2):
            observed.append(self.manager.get(0, index=i))
        for obj in observed:
            self.assertEqual(obj.filename, self.obj_fn)
            self.assertEqual(obj.mode, self.obj_mode)
            self.assertEqual(obj.options, self.obj_options)

    def test_get_object_raises_error_if_index_is_not_specified(self):
        for i in range(2):
            self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i)
        with self.assertRaises(TypeError):
            self.manager.get(0)

    def test_can_update_object(self):
        objects = []
        for i in range(2):
            objects.append(self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i))
        for index, obj in enumerate(objects):
            self.assertEqual(obj.options['target-device'], '/dev/sda')
            self.manager.update(0, 'target-device', '/dev/sdb', index=index)
            self.assertEqual(obj.options['target-device'], '/dev/sdb')

    def test_update_object_raises_error_if_index_is_not_specified(self):
        for i in range(2):
            self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i)
        with self.assertRaises(TypeError):
            self.manager.update(0, 'target-device', '/dev/sdb')

    def test_can_remove_object(self):
        for i in range(2):
            self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i)
        for installation_set in self.manager:
            self.assertEqual(len(installation_set), 1)
        for i in range(2):
            self.manager.remove(0, index=i)
        for installation_set in self.manager:
            self.assertEqual(len(installation_set), 0)

    def test_remove_object_raises_error_if_index_is_not_specified(self):
        for i in range(2):
            self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i)
        with self.assertRaises(TypeError):
            self.manager.remove(0)

    def test_can_get_all_objects(self):
        expected = []
        for i in range(2):
            expected.append(self.manager.add(
                self.obj_fn, self.obj_mode, options=self.obj_options, index=i))
        observed = list(self.manager.all())
        self.assertEqual(expected, observed)
