# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import unittest
from unittest.mock import Mock, patch

from uhu.core.objects import (
    InstallationSet, ObjectsManager, InstallationSetMode)


def verify_all_modes(fn):
    """Run decorated test against all installation set modes."""
    def wrapper(*args, **kwargs):
        for mode in InstallationSetMode:
            fn(*args, mode=mode, **kwargs)
    return wrapper


class InstallationSetModeTestCase(unittest.TestCase):

    def test_can_return_mode_from_objects_set(self):
        single = InstallationSetMode.from_objects([[]])
        self.assertEqual(single, InstallationSetMode.Single)

        active_inactive = InstallationSetMode.from_objects([[], []])
        self.assertEqual(active_inactive, InstallationSetMode.ActiveInactive)

    def test_raises_error_if_objects_is_empty(self):
        with self.assertRaises(ValueError):
            InstallationSetMode.from_objects([])


class ObjectsManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.options = {
            'filename': __file__,
            'target-type': 'device',
            'target': '/dev/sda',
        }

    @verify_all_modes
    def test_can_create_managers(self, mode):
        manager = ObjectsManager(mode)
        self.assertEqual(manager.mode, mode)
        self.assertEqual(len(manager), mode.value)

    @verify_all_modes
    def test_installation_set_as_metadata(self, mode):
        manager = ObjectsManager(mode)
        manager.create('raw', self.options)
        metadata = manager.metadata()
        self.assertEqual(len(metadata), mode.value)
        for index, installation_set in enumerate(manager):
            self.assertEqual(metadata[index], installation_set.metadata())

    @verify_all_modes
    def test_installation_set_as_template(self, mode):
        manager = ObjectsManager(mode)
        manager.create('raw', self.options)
        template = manager.template()
        self.assertEqual(len(template), mode.value)
        for index, installation_set in enumerate(manager):
            self.assertEqual(template[index], installation_set.template())

    @verify_all_modes
    def test_installation_set_manager_as_string(self, mode):
        self.addCleanup(os.chdir, os.getcwd())
        fixtures_dir = 'fixtures'
        os.chdir(os.path.join(os.path.dirname(__file__), fixtures_dir))
        manager = ObjectsManager(mode)
        self.options['filename'] = 'manager.txt'
        manager.create('raw', self.options)
        fn = '{}-mode.txt'.format(mode.name.lower())
        with open(fn) as fp:
            self.assertEqual(str(manager), fp.read())

    def test_is_single_returns_True_when_single(self):
        manager = ObjectsManager(InstallationSetMode.Single)
        self.assertTrue(manager.is_single())

    def test_is_single_returns_False_when_not_single(self):
        manager = ObjectsManager(InstallationSetMode.ActiveInactive)
        self.assertFalse(manager.is_single())

    @verify_all_modes
    def test_can_get_installation_set(self, mode):
        manager = ObjectsManager(mode)
        installation_set = manager.get_installation_set(0)
        self.assertIsInstance(installation_set, InstallationSet)

    @verify_all_modes
    def test_get_installation_set_raises_error_if_invalid_index(self, mode):
        manager = ObjectsManager(mode)
        with self.assertRaises(ValueError):
            manager.get_installation_set(100)

    @verify_all_modes
    def test_can_create_object(self, mode):
        manager = ObjectsManager(mode)
        self.assertEqual(len(manager.all()), 0)
        index = manager.create('raw', self.options)
        self.assertEqual(len(manager.all()), mode.value * 1)
        for set_index, installation_set in enumerate(manager):
            self.assertEqual(len(installation_set), 1)
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)
            self.assertEqual(obj.mode, 'raw')
            self.assertEqual(obj['target'], '/dev/sda')

    def test_can_create_object_with_different_values(self):
        manager = ObjectsManager(InstallationSetMode.ActiveInactive)
        self.assertEqual(len(manager.all()), 0)
        self.options['target'] = ('/dev/sda', '/dev/sdb')
        index = manager.create('raw', self.options)
        obj0 = manager.get(index=0, installation_set=0)
        obj1 = manager.get(index=0, installation_set=1)
        self.assertEqual(obj0['target'], '/dev/sda')
        self.assertEqual(obj1['target'], '/dev/sdb')

    @verify_all_modes
    def test_can_get_object(self, mode):
        manager = ObjectsManager(mode)
        index = manager.create('raw', self.options)
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)
            self.assertEqual(obj.mode, 'raw')
            self.assertEqual(obj['target'], '/dev/sda')

    @verify_all_modes
    def test_can_update_asymmetrical_object_option(self, mode):
        manager = ObjectsManager(mode)
        index = manager.create('raw', self.options)
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
    def test_can_update_symmetrical_object_option(self, mode):
        manager = ObjectsManager(mode)
        index = manager.create('raw', self.options)
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)

        manager.update(
            index=0, option='filename', value='new-filename')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, 'new-filename')

    @verify_all_modes
    def test_update_asymmetrical_option_raises_without_install_set(self, mode):
        manager = ObjectsManager(mode)
        index = manager.create('raw', self.options)

        with self.assertRaises(ValueError):
            manager.update(index, 'target', '/dev/sdb')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj['target'], '/dev/sda')

    @verify_all_modes
    def test_update_symmetrical_option_raises_error_if_install_set(self, mode):
        manager = ObjectsManager(mode)
        self.options['count'] = 100
        index = manager.create('raw', self.options)
        with self.assertRaises(ValueError):
            manager.update(index, 'count', 200, installation_set=0)

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj['count'], 100)

    @verify_all_modes
    def test_can_remove_object(self, mode):
        manager = ObjectsManager(mode)
        index = manager.create('raw', self.options)
        self.assertEqual(len(manager.all()), 1 * mode.value)
        manager.remove(index)
        self.assertEqual(len(manager.all()), 0)

    @verify_all_modes
    def test_can_get_all_objects(self, mode):
        manager = ObjectsManager(mode)
        index = manager.create('raw', self.options)
        expected = [set_.get(index) for set_ in manager]
        observed = manager.all()
        self.assertEqual(observed, expected)
