# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from uhu.repl.repl import UHURepl
from uhu.repl import functions


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = UHURepl()


class PackageTestCase(BaseTestCase):

    def test_can_save_package(self):
        self.repl.arg = '/tmp/uhu_dump.json'
        self.addCleanup(os.remove, self.repl.arg)
        functions.save_package(self.repl)
        self.assertTrue(os.path.exists(self.repl.arg))

    def test_save_package_raises_error_if_missing_arg(self):
        with self.assertRaises(ValueError):
            functions.save_package(self.repl)

    def test_can_show_package(self):
        self.repl.package.__str__ = Mock()
        functions.show_package(self.repl)
        self.assertTrue(self.repl.package.__str__)

    def test_can_set_a_version(self):
        self.assertIsNone(self.repl.package.version)
        self.repl.arg = '2.0'
        functions.set_package_version(self.repl)
        self.assertEqual(self.repl.package.version, '2.0')

    def test_set_raises_error_if_arg_is_not_specified(self):
        with self.assertRaises(ValueError):
            functions.set_package_version(self.repl)


class ObjectManagementTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.options = {
            'filename': __file__,
            'target-type': 'device',
            'target': '/dev/sda',
        }

    @patch('uhu.repl.helpers.prompt')
    def test_can_add_object(self, prompt):
        values = [
            'copy',
            __file__,
            'device',  # target type
            '/dev/sda',  # target (set 0)
            '/dev/sdb',  # target (set 1)
            '/home/user1',  # target path (set 0)
            '/home/user2',  # target path (set 1)
            'ext4',  # filesystem
            '',  # mount options
            '',  # format device
            '',  # install condition (always)
        ]
        prompt.side_effect = values
        self.assertEqual(len(self.repl.package.objects.all()), 0)
        functions.add_object(self.repl)
        self.assertEqual(len(self.repl.package.objects.all()), 2)
        obj0 = self.repl.package.objects.get(index=0, installation_set=0)
        obj1 = self.repl.package.objects.get(index=0, installation_set=1)
        self.assertEqual(obj0['target'], '/dev/sda')
        self.assertEqual(obj1['target'], '/dev/sdb')
        self.assertEqual(obj0['target-path'], '/home/user1')
        self.assertEqual(obj1['target-path'], '/home/user2')

    @patch('uhu.repl.helpers.prompt')
    def test_can_remove_object_using_uid(self, prompt):
        prompt.side_effect = ['0']
        self.repl.package.objects.create('raw', self.options)
        self.assertEqual(len(self.repl.package.objects.all()), 2)
        functions.remove_object(self.repl)
        self.assertEqual(len(self.repl.package.objects.all()), 0)

    @patch('uhu.repl.helpers.prompt')
    def test_can_remove_object_using_autocompleter_suggestion(self, prompt):
        prompt.side_effect = ['0# {}'.format(__file__)]
        self.repl.package.objects.create('raw', self.options)
        self.assertEqual(len(self.repl.package.objects.all()), 2)
        functions.remove_object(self.repl)
        self.assertEqual(len(self.repl.package.objects.all()), 0)

    @patch('uhu.repl.helpers.prompt')
    def test_remove_object_raises_error_if_invalid_uid(self, prompt):
        prompt.side_effect = ['invalid']
        with self.assertRaises(ValueError):
            functions.remove_object(self.repl)

    @patch('uhu.repl.helpers.prompt')
    def test_can_edit_asymmetrical_option(self, prompt):
        prompt.side_effect = [
            '0',  # object index
            'target',  # option
            '0',  # installation set index
            '/dev/sdb',  # value
        ]
        index = self.repl.package.objects.create('raw', self.options)
        for set_index in range(len(self.repl.package.objects)):
            obj = self.repl.package.objects.get(
                index=index, installation_set=set_index)
            self.assertEqual(obj['target'], '/dev/sda')

        functions.edit_object(self.repl)

        obj = self.repl.package.objects.get(index=index, installation_set=0)
        self.assertEqual(obj['target'], '/dev/sdb')

        obj = self.repl.package.objects.get(index=index, installation_set=1)
        self.assertEqual(obj['target'], '/dev/sda')

    @patch('uhu.repl.helpers.prompt')
    def test_can_edit_symmetrical_option(self, prompt):
        prompt.side_effect = [
            '0',  # object index
            'count',  # option
            '200',  # value
        ]
        self.options['count'] = 100
        index = self.repl.package.objects.create('raw', self.options)
        for set_index in range(len(self.repl.package.objects)):
            obj = self.repl.package.objects.get(
                index=index, installation_set=set_index)
            self.assertEqual(obj['count'], 100)

        functions.edit_object(self.repl)

        for set_index in range(len(self.repl.package.objects)):
            obj = self.repl.package.objects.get(
                index=index, installation_set=set_index)
            self.assertEqual(obj['count'], 200)

    @patch('uhu.repl.helpers.prompt')
    def test_can_edit_object_filename(self, prompt):
        self.repl.package.objects.create('raw', self.options)
        with tempfile.NamedTemporaryFile() as fp:
            prompt.side_effect = [
                '0',  # object index
                'filename',  # option
                fp.name,  # value
            ]
            obj = self.repl.package.objects.get(index=0, installation_set=1)
            self.assertEqual(obj.filename, __file__)
            functions.edit_object(self.repl)
            self.assertEqual(obj.filename, fp.name)

    @patch('uhu.repl.helpers.prompt')
    def test_edit_object_raises_error_if_invalid_uid(self, prompt):
        prompt.side_effect = ['23']
        with self.assertRaises(ValueError):
            functions.edit_object(self.repl)

    @patch('uhu.repl.helpers.prompt')
    def test_edit_object_raises_error_if_invalid_option(self, prompt):
        prompt.side_effect = ['1', 'invalid']
        self.repl.package.objects.create('raw', self.options)
        with self.assertRaises(ValueError):
            functions.edit_object(self.repl)


class HardwareManagementTestCase(BaseTestCase):

    @patch('uhu.repl.functions.prompt')
    def test_can_add_hardware_without_revision(self, prompt):
        prompt.side_effect = ['PowerX', '']
        self.assertEqual(self.repl.package.hardwares.count(), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        hardware = self.repl.package.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 0)

    @patch('uhu.repl.functions.prompt')
    def test_can_add_hardware_with_revision(self, prompt):
        functions.prompt.side_effect = ['PowerX', 'rev.1']
        self.assertEqual(self.repl.package.hardwares.count(), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        hardware = self.repl.package.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 1)

    @patch('uhu.repl.functions.prompt')
    def test_can_add_multiple_hardwares_and_revisions(self, prompt):
        functions.prompt.side_effect = ['PowerX PowerY', 'PX1 PX2', 'PY1']
        self.assertEqual(self.repl.package.hardwares.count(), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 2)
        hardware_1 = self.repl.package.hardwares.get('PowerX')
        self.assertEqual(len(hardware_1['revisions']), 2)
        hardware_2 = self.repl.package.hardwares.get('PowerY')
        self.assertEqual(len(hardware_2['revisions']), 1)

    @patch('uhu.repl.functions.prompt')
    def test_can_remove_supported_hardware(self, prompt):
        functions.prompt.side_effect = ['PowerX', '']
        self.repl.package.hardwares.add('PowerX')
        self.repl.package.hardwares.add('PowerY')
        self.assertEqual(self.repl.package.hardwares.count(), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        self.assertIsNone(self.repl.package.hardwares.get('PowerX'))

    @patch('uhu.repl.functions.prompt')
    def test_can_remove_many_supported_hardwares(self, prompt):
        functions.prompt.side_effect = ['PowerX PowerY', '', '']
        self.repl.package.hardwares.add('PowerX')
        self.repl.package.hardwares.add('PowerY')
        self.assertEqual(self.repl.package.hardwares.count(), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 0)

    @patch('uhu.repl.functions.prompt')
    def test_can_remove_only_one_hardware_revision(self, prompt):
        functions.prompt.side_effect = ['PowerX', '1']
        self.repl.package.hardwares.add('PowerX', revisions=['1', '2'])
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        hardware = self.repl.package.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        self.assertEqual(len(hardware['revisions']), 1)

    @patch('uhu.repl.functions.prompt')
    def test_can_remove_many_hardware_revisions(self, prompt):
        functions.prompt.side_effect = ['PowerX', '1 2']
        self.repl.package.hardwares.add('PowerX', revisions=['1', '2'])
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        hardware = self.repl.package.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(self.repl.package.hardwares.count(), 1)
        self.assertEqual(len(hardware['revisions']), 0)
