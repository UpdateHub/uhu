# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

from efu.core.hardware import HardwareManager


class HardwareManagerTestCase(unittest.TestCase):

    def test_can_add_hardware(self):
        manager = HardwareManager()
        self.assertEqual(manager.count(), 0)
        manager.add(name='PowerX', revisions=['PX230'])
        self.assertEqual(manager.count(), 1)
        hardware = manager.get('PowerX')
        self.assertEqual(hardware['name'], 'PowerX')
        self.assertEqual(hardware['revisions'], ['PX230'])

    def test_can_remove_hardware(self):
        manager = HardwareManager()
        manager.add(name='PowerX')
        manager.add(name='PowerY')
        self.assertEqual(manager.count(), 2)
        manager.remove('PowerX')
        self.assertEqual(manager.count(), 1)
        manager.remove('PowerY')
        self.assertEqual(manager.count(), 0)

    def test_remove_hardware_raises_error_if_invalid_hardware(self):
        manager = HardwareManager()
        with self.assertRaises(ValueError):
            manager.remove('dosnt-exist')

    def test_can_add_hardware_revision(self):
        manager = HardwareManager()
        manager.add(name='PowerX', revisions=['PX230'])
        manager.add_revision('PowerX', 'PX240')
        revisions = manager.get('PowerX')['revisions']
        self.assertEqual(revisions, ['PX230', 'PX240'])

    def test_add_hardware_revision_raises_error_if_invalid_hardware(self):
        manager = HardwareManager()
        with self.assertRaises(ValueError):
            manager.add_revision('dosnt-exist', 'revision')

    def test_can_remove_hardware_revision(self):
        manager = HardwareManager()
        manager.add(name='PowerX', revisions=['PX240'])
        self.assertEqual(len(manager.get('PowerX')['revisions']), 1)
        manager.remove_revision('PowerX', 'PX240')
        self.assertEqual(len(manager.get('PowerX')['revisions']), 0)

    def test_remove_hardware_revision_raises_error_if_invalid_hardware(self):
        manager = HardwareManager()
        with self.assertRaises(ValueError):
            manager.remove_revision('bad-hardware', 'revision')

    def test_remove_hardware_revision_raises_error_if_invalid_revision(self):
        manager = HardwareManager()
        manager.add('PowerX')
        with self.assertRaises(ValueError):
            manager.remove_revision('PowerX', 'bad-revision')

    def test_hardware_revisions_are_alphanumeric_sorted(self):
        manager = HardwareManager()
        manager.add(name='PowerX', revisions=['PX240'])
        manager.add_revision('PowerX', 'PX250')
        manager.add_revision('PowerX', 'PX230')
        expected = ['PX230', 'PX240', 'PX250']
        observed = manager.get('PowerX')['revisions']
        self.assertEqual(observed, expected)

    def test_entries_are_not_duplicated_when_adding_same_hardware_twice(self):
        manager = HardwareManager()
        manager.add(name='PowerX', revisions=['PX230'])
        manager.add(name='PowerX', revisions=['PX230'])
        self.assertEqual(manager.count(), 1)
        self.assertEqual(len(manager.get('PowerX')['revisions']), 1)

    def test_can_serialize_manager_as_template(self):
        manager = HardwareManager()
        manager.add(name='PowerX', revisions=['PX230'])
        template = manager.template()
        self.assertEqual(len(template), 1)
        self.assertEqual(template['PowerX']['name'], 'PowerX')
        self.assertEqual(template['PowerX']['revisions'], ['PX230'])

    def test_can_serialize_as_metadata(self):
        manager = HardwareManager()
        manager.add(name='PowerX')
        manager.add(name='PowerY', revisions=['PY250', 'PY240', 'PY230'])
        manager.add(name='PowerZ', revisions=['PZ230'])
        expected = [
            {
                'hardware': 'PowerX'
            },
            {
                'hardware': 'PowerY',
                'hardware-rev': 'PY230'
            },
            {
                'hardware': 'PowerY',
                'hardware-rev': 'PY240'
            },
            {
                'hardware': 'PowerY',
                'hardware-rev': 'PY250'
            },
            {
                'hardware': 'PowerZ',
                'hardware-rev': 'PZ230'
            },
        ]
        observed = manager.metadata()
        self.assertEqual(observed, expected)

    def test_can_serialize_manager_as_string(self):
        manager = HardwareManager()
        manager.add(name='PowerX')
        manager.add(name='PowerY', revisions=['PY230'])
        manager.add(name='PowerZ', revisions=['PZ250', 'PZ240', 'PZ230'])
        with open('tests/fixtures/hardware/manager.txt') as fp:
            expected = fp.read()
        observed = str(manager)
        self.assertEqual(observed, expected)

    def test_can_serialize_empty_manager_as_string(self):
        manager = HardwareManager()
        with open('tests/fixtures/hardware/manager_empty.txt') as fp:
            expected = fp.read().strip()
        observed = str(manager)
        self.assertEqual(observed, expected)
