# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest
from unittest.mock import Mock, patch

from efu.core import installation_set
from efu.core.installation_set import (
    InstallationSet, InstallationSetManager, InstallationSetMode)


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


class InstallationSetManagerTestCase(unittest.TestCase):

    @verify_all_modes
    def test_can_create_managers(self, mode):
        manager = InstallationSetManager(mode)
        self.assertEqual(manager.mode, mode)
        self.assertEqual(len(manager), mode.value)

    @verify_all_modes
    def test_installation_set_as_metadata(self, mode):
        manager = InstallationSetManager(mode)
        manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        metadata = manager.metadata()
        self.assertEqual(len(metadata), mode.value)
        for index, installation_set in enumerate(manager):
            self.assertEqual(metadata[index], installation_set.metadata())

    @verify_all_modes
    def test_installation_set_as_template(self, mode):
        manager = InstallationSetManager(mode)
        manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        template = manager.template()
        self.assertEqual(len(template), mode.value)
        for index, installation_set in enumerate(manager):
            self.assertEqual(template[index], installation_set.template())

    @verify_all_modes
    def test_installation_set_manager_as_string(self, mode):
        self.addCleanup(os.chdir, os.getcwd())
        fixtures_dir = '../fixtures/installation_set'
        os.chdir(os.path.join(os.path.dirname(__file__), fixtures_dir))
        manager = InstallationSetManager(mode)
        manager.create('manager.txt', 'raw', {'target-device': '/dev/sda'})
        fn = '{}-mode.txt'.format(mode.name.lower())
        with open(fn) as fp:
            self.assertEqual(str(manager), fp.read())

    def test_is_single_returns_True_when_single(self):
        manager = InstallationSetManager(InstallationSetMode.Single)
        self.assertTrue(manager.is_single())

    def test_is_single_returns_False_when_not_single(self):
        manager = InstallationSetManager(InstallationSetMode.ActiveInactive)
        self.assertFalse(manager.is_single())

    @verify_all_modes
    def test_can_get_installation_set(self, mode):
        manager = InstallationSetManager(mode)
        installation_set = manager.get_installation_set(0)
        self.assertIsInstance(installation_set, InstallationSet)

    @verify_all_modes
    def test_get_installation_set_raises_error_if_invalid_index(self, mode):
        manager = InstallationSetManager(mode)
        with self.assertRaises(ValueError):
            manager.get_installation_set(100)

    @verify_all_modes
    def test_can_create_object(self, mode):
        manager = InstallationSetManager(mode)
        self.assertEqual(len(manager.all()), 0)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        self.assertEqual(len(manager.all()), mode.value * 1)
        for set_index, installation_set in enumerate(manager):
            self.assertEqual(len(installation_set), 1)
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)
            self.assertEqual(obj.mode, 'raw')
            self.assertEqual(obj.options['target-device'], '/dev/sda')

    @verify_all_modes
    def test_can_get_object(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.filename, __file__)
            self.assertEqual(obj.mode, 'raw')
            self.assertEqual(obj.options['target-device'], '/dev/sda')

    @verify_all_modes
    def test_can_update_asymmetrical_object_option(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.options['target-device'], '/dev/sda')

        manager.update(
            index=0, installation_set=0,
            option='target-device', value='/dev/sdb')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            if set_index == 0:
                self.assertEqual(obj.options['target-device'], '/dev/sdb')
            else:
                self.assertEqual(obj.options['target-device'], '/dev/sda')

    @verify_all_modes
    def test_can_update_symmetrical_object_option(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
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
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})

        with self.assertRaises(ValueError):
            manager.update(index, 'target-device', '/dev/sdb')

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.options['target-device'], '/dev/sda')

    @verify_all_modes
    def test_update_symmetrical_option_raises_error_if_install_set(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {
            'target-device': '/dev/sda',
            'count': 100,
        })

        with self.assertRaises(ValueError):
            manager.update(index, 'count', 200, installation_set=0)

        for set_index, installation_set in enumerate(manager):
            obj = manager.get(index=index, installation_set=set_index)
            self.assertEqual(obj.options['count'], 100)

    @verify_all_modes
    def test_can_remove_object(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        self.assertEqual(len(manager.all()), 1 * mode.value)
        manager.remove(index)
        self.assertEqual(len(manager.all()), 0)

    @verify_all_modes
    def test_can_get_all_objects(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        expected = [set_.get(index) for set_ in manager]
        observed = manager.all()
        self.assertEqual(observed, expected)

    @verify_all_modes
    def test_can_use_cache_to_load_objects(self, mode):
        manager = InstallationSetManager(mode)
        index = manager.create(__file__, 'raw', {'target-device': '/dev/sda'})
        cache = {
            __file__: {
                'size': 100,
                'md5': 'md5',
                'sha256sum': 'sha256sum',
                'version': '2.0',
            }
        }
        patched_dict = Mock()
        patched_dict.return_value = cache
        with patch.dict(installation_set.__builtins__, {'dict': patched_dict}):
            manager.load()
            for set_ in manager:
                for obj in set_:
                    self.assertEqual(obj.size, 100)
                    self.assertEqual(obj.md5, 'md5')
                    self.assertEqual(obj.sha256sum, 'sha256sum')
                    self.assertEqual(obj.version, '2.0')
