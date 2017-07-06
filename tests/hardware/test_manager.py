# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest

from uhu.core.hardware import (
    SupportedHardwareManager, ANY, SUPPORTED_HARDWARE_ERROR)


class SupportedHardwareConstructors(unittest.TestCase):

    def test_can_construct_from_dump_when_any(self):
        manager = SupportedHardwareManager(dump={
            'supported-hardware': ANY,
        })
        self.assertEqual(len(manager), 0)

    def test_can_construct_from_dump_when_some(self):
        manager = SupportedHardwareManager(dump={
            'supported-hardware': ['h1', 'h2'],
        })
        self.assertEqual(len(manager), 2)
        self.assertIn('h1', manager)
        self.assertIn('h2', manager)

    def test_construct_from_dump_raises_error_when_invalid(self):
        invalid_dumps = [
            {},
            {'supported-hardware': None},
            {'supported-hardware': 'other'},
            {'supported-hardware': 42},
        ]
        for dump in invalid_dumps:
            with self.assertRaises(ValueError, msg=SUPPORTED_HARDWARE_ERROR):
                SupportedHardwareManager(dump=dump)


class SupportedHardwareSerialization(unittest.TestCase):

    def test_can_serialize_as_template_when_some(self):
        manager = SupportedHardwareManager()
        manager.add('PowerX')
        expected = {'supported-hardware': ['PowerX']}
        observed = manager.to_template()
        self.assertEqual(expected, observed)

    def test_can_serialize_as_template_when_any(self):
        manager = SupportedHardwareManager()
        expected = {'supported-hardware': 'any'}
        observed = manager.to_template()
        self.assertEqual(expected, observed)

    def test_can_serialize_as_metadata_when_some(self):
        manager = SupportedHardwareManager()
        manager.add('PowerZ')
        manager.add('PowerY')
        manager.add('PowerX')
        expected = {'supported-hardware': ['PowerX', 'PowerY', 'PowerZ']}
        observed = manager.to_metadata()
        self.assertEqual(observed, expected)

    def test_can_serialize_as_metadata_when_any(self):
        manager = SupportedHardwareManager()
        expected = {'supported-hardware': 'any'}
        observed = manager.to_metadata()
        self.assertEqual(observed, expected)

    def test_can_serialize_manager_as_string_when_some(self):
        manager = SupportedHardwareManager()
        manager.add('PowerX')
        manager.add('PowerY')
        manager.add('PowerZ')
        with open('tests/hardware/fixtures/string_some.txt') as fp:
            expected = fp.read().strip()
        observed = str(manager)
        self.assertEqual(observed, expected)

    def test_can_serialize_manager_as_string_when_any(self):
        manager = SupportedHardwareManager()
        with open('tests/hardware/fixtures/string_any.txt') as fp:
            expected = fp.read().strip()
        observed = str(manager)
        self.assertEqual(observed, expected)


class SupportedHardwareManagement(unittest.TestCase):

    def test_can_add_hardware_identifier(self):
        manager = SupportedHardwareManager()
        hardware = 'PowerX'
        self.assertEqual(len(manager), 0)
        manager.add(hardware)
        self.assertEqual(len(manager), 1)
        self.assertIn(hardware, manager)

    def test_cant_add_same_hardware_identifier_twice(self):
        manager = SupportedHardwareManager()
        manager.add('PowerX')
        manager.add('PowerX')
        self.assertEqual(len(manager), 1)

    def test_can_remove_hardware_identifier(self):
        manager = SupportedHardwareManager()
        manager.add('PowerX')
        manager.add('PowerY')
        self.assertEqual(len(manager), 2)
        manager.remove('PowerX')
        self.assertEqual(len(manager), 1)
        manager.remove('PowerY')
        self.assertEqual(len(manager), 0)

    def test_cant_remove_unknown_hardware_identifier(self):
        manager = SupportedHardwareManager()
        with self.assertRaises(KeyError):
            manager.remove('unknown-hardware')
