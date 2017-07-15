# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import unittest
from unittest.mock import Mock, patch

from uhu.core.object import Object
from uhu.core.objects import InstallationSet, ObjectsManager


def verify_all_modes(fn):
    """Run decorated test against all installation set modes."""
    def wrapper(*args, **kwargs):
        for n in range(1, 3):
            fn(*args, sets=n, **kwargs)
    return wrapper


class ObjectsManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.options = {
            'filename': __file__,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
        }

    @verify_all_modes
    def test_can_create_managers(self, sets):
        manager = ObjectsManager(sets)
        self.assertEqual(len(manager), sets)

    def test_can_only_create_manager_with_one_or_two_sets(self):
        for n_sets in [-1, 0, 3, 4]:
            with self.assertRaises(ValueError):
                ObjectsManager(n_sets)

    @verify_all_modes
    def test_can_create_manager_from_dump(self, sets):
        dump = {ObjectsManager.metadata: [[self.options] for _ in range(sets)]}
        manager = ObjectsManager(dump=dump)
        self.assertEqual(len(manager), sets)
        for set_ in manager:
            self.assertEqual(set_, InstallationSet([self.options]))

    def test_create_from_dump_raises_error_if_missing_objects(self):
        with self.assertRaises(ValueError):
            ObjectsManager(dump={})

    def test_create_from_dump_raises_error_if_invalid_type(self):
        with self.assertRaises(TypeError):
            ObjectsManager(dump={ObjectsManager.metadata: 1})

    @verify_all_modes
    def test_installation_set_as_metadata(self, sets):
        manager = ObjectsManager(sets)
        manager.create(self.options)
        metadata = manager.to_metadata()[manager.metadata]
        self.assertEqual(len(metadata), sets)
        for index, installation_set in enumerate(manager):
            self.assertEqual(metadata[index], installation_set.to_metadata())

    @verify_all_modes
    def test_installation_set_as_template(self, sets):
        manager = ObjectsManager(sets)
        manager.create(self.options)
        template = manager.to_template()[manager.metadata]
        self.assertEqual(len(template), sets)
        for index, installation_set in enumerate(manager):
            self.assertEqual(template[index], installation_set.to_template())

    @verify_all_modes
    def test_installation_set_manager_as_string(self, sets):
        self.addCleanup(os.chdir, os.getcwd())
        fixtures_dir = 'fixtures/objects'
        os.chdir(os.path.join(os.path.dirname(__file__), fixtures_dir))
        manager = ObjectsManager(sets)
        self.options['filename'] = 'manager.txt'
        manager.create(self.options)
        name = 'single' if sets == 1 else 'activeinactive'
        fn = '{}-mode.txt'.format(name)
        with open(fn) as fp:
            expected = fp.read().strip()
        self.assertEqual(str(manager), expected)

    def test_installation_set_manager_as_string_when_empty(self):
        manager = ObjectsManager()
        self.assertEqual(str(manager), 'Objects: None')

    def test_is_single_returns_True_when_single(self):
        manager = ObjectsManager(1)
        self.assertTrue(manager.is_single())

    def test_is_single_returns_False_when_not_single(self):
        manager = ObjectsManager(2)
        self.assertFalse(manager.is_single())

    @verify_all_modes
    def test_can_get_installation_set(self, sets):
        manager = ObjectsManager(sets)
        installation_set = manager[0]
        self.assertIsInstance(installation_set, InstallationSet)

    @verify_all_modes
    def test_get_installation_set_raises_error_if_missing_index(self, sets):
        manager = ObjectsManager(sets)
        with self.assertRaises(IndexError):
            manager[100]

    @verify_all_modes
    def test_get_installation_set_raises_error_if_invalid_index(self, sets):
        manager = ObjectsManager(sets)
        with self.assertRaises(TypeError):
            manager['invalid-index']

    @verify_all_modes
    def test_can_create_object(self, sets):
        manager = ObjectsManager(sets)
        self.assertEqual(len(manager.all()), 0)
        index = manager.create(self.options)
        self.assertEqual(len(manager.all()), sets * 1)
        for set_index, installation_set in enumerate(manager):
            self.assertEqual(len(installation_set), 1)
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)
            self.assertEqual(obj.mode, 'raw')
            self.assertEqual(obj['target'], '/dev/sda')

    def test_can_create_object_with_different_values(self):
        manager = ObjectsManager(2)
        self.assertEqual(len(manager.all()), 0)
        self.options['target'] = ('/dev/sda', '/dev/sdb')
        index = manager.create(self.options)
        obj0 = manager.get(index=0, installation_set=0)
        obj1 = manager.get(index=0, installation_set=1)
        self.assertEqual(obj0['target'], '/dev/sda')
        self.assertEqual(obj1['target'], '/dev/sdb')

    @verify_all_modes
    def test_can_get_object(self, sets):
        manager = ObjectsManager(sets)
        index = manager.create(self.options)
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)
            self.assertEqual(obj.mode, 'raw')
            self.assertEqual(obj['target'], '/dev/sda')

    @verify_all_modes
    def test_can_update_asymmetrical_object_option(self, sets):
        manager = ObjectsManager(sets)
        index = manager.create(self.options)
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj['target'], '/dev/sda')

        manager.update(
            index=0, installation_set=0,
            option='target', value='/dev/sdb')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            if set_index == 0:
                self.assertEqual(obj['target'], '/dev/sdb')
            else:
                self.assertEqual(obj['target'], '/dev/sda')

    @verify_all_modes
    def test_can_update_symmetrical_object_option(self, sets):
        manager = ObjectsManager(sets)
        index = manager.create(self.options)
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)

        manager.update(
            index=0, option='filename', value='new-filename')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, 'new-filename')

    @verify_all_modes
    def test_update_asymmetrical_option_raises_without_install_set(self, sets):
        manager = ObjectsManager(sets)
        index = manager.create(self.options)

        with self.assertRaises(ValueError):
            manager.update(index, 'target', '/dev/sdb')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj['target'], '/dev/sda')

    @verify_all_modes
    def test_update_symmetrical_option_raises_error_if_install_set(self, sets):
        manager = ObjectsManager(sets)
        self.options['count'] = 100
        index = manager.create(self.options)
        with self.assertRaises(ValueError):
            manager.update(index, 'count', 200, installation_set=0)

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj['count'], 100)

    @verify_all_modes
    def test_can_remove_object(self, sets):
        manager = ObjectsManager(sets)
        index = manager.create(self.options)
        self.assertEqual(len(manager.all()), 1 * sets)
        manager.remove(index)
        self.assertEqual(len(manager.all()), 0)

    @verify_all_modes
    def test_can_get_all_objects(self, sets):
        manager = ObjectsManager(sets)
        index = manager.create(self.options)
        expected = [set_.get(index) for set_ in manager]
        observed = manager.all()
        self.assertEqual(observed, expected)

    @verify_all_modes
    def test_can_compare_managers(self, sets):
        manager1 = ObjectsManager()
        manager2 = ObjectsManager()
        self.assertEqual(manager1, manager2)
        manager1.create(self.options)
        self.assertNotEqual(manager1, manager2)
        manager2.create(self.options)
        self.assertEqual(manager1, manager2)


class InstallationSetTestCase(unittest.TestCase):

    def setUp(self):
        self.fn = __file__
        self.mode = 'raw'
        self.options = {
            'filename': __file__,
            'mode': self.mode,
            'target-type': 'device',
            'target': '/dev/sda',
        }
        self.obj = Object(self.options)

    def test_can_create_object(self):
        installation_set = InstallationSet()
        self.assertEqual(len(installation_set), 0)
        index = installation_set.create(self.options)
        self.assertEqual(index, 0)
        self.assertEqual(len(installation_set), 1)
        obj = installation_set.get(index)
        self.assertEqual(obj.filename, self.fn)
        self.assertEqual(obj.mode, self.mode)
        self.assertEqual(obj['target'], '/dev/sda')

    def test_can_get_object_by_index(self):
        installation_set = InstallationSet()
        installation_set.create(self.options)
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
        index = installation_set.create(self.options)
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
        index = installation_set.create(self.options)
        self.assertEqual(len(installation_set), 1)
        installation_set.remove(index)
        self.assertEqual(len(installation_set), 0)

    def test_remove_object_raises_error_with_invalid_index(self):
        installation_set = InstallationSet()
        with self.assertRaises(ValueError):
            installation_set.remove(100)

    def test_installation_set_as_metadata(self):
        installation_set = InstallationSet()
        installation_set.create(self.options)
        metadata = installation_set.to_metadata()
        self.assertEqual(len(metadata), 1)
        # First object metadata
        self.assertEqual(metadata[0], self.obj.to_metadata())

    def test_installation_set_as_template(self):
        installation_set = InstallationSet()
        installation_set.create(self.options)
        template = installation_set.to_template()
        self.assertEqual(len(template), 1)
        # First object template
        self.assertEqual(template[0], self.obj.to_template())

    def test_installation_set_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/core/fixtures/objects')
        self.addCleanup(os.chdir, cwd)
        with open('set.txt') as fp:
            expected = fp.read()
        installation_set = InstallationSet()
        self.options['filename'] = 'set.txt'
        for _ in range(3):
            installation_set.create(self.options)
        self.assertEqual(str(installation_set), expected)
