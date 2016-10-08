# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import unittest
from unittest.mock import Mock

from efu.repl.repl import EFURepl
from efu.repl import functions


class PackageTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = EFURepl()
        functions.prompt = Mock()

    def test_can_save_package(self):
        self.repl.arg = '/tmp/efu_dump.json'
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

    def test_can_add_object(self):
        values = [__file__, 'copy', '/', '/', 'ext4', '', '', '']
        functions.prompt.side_effect = values
        self.assertEqual(len(self.repl.package), 0)
        functions.add_object(self.repl)
        self.assertEqual(len(self.repl.package), 1)

    def test_add_object_raises_error_if_missing_filename(self):
        functions.prompt.side_effect = ['']
        with self.assertRaises(ValueError):
            functions.add_object(self.repl)

    def test_add_object_raises_error_if_file_does_not_exist(self):
        functions.prompt.side_effect = ['not-exist']
        with self.assertRaises(ValueError):
            functions.add_object(self.repl)

    def test_add_object_raises_error_if_filename_is_a_dir(self):
        functions.prompt.side_effect = ['/']
        with self.assertRaises(ValueError):
            functions.add_object(self.repl)

    def test_add_object_raises_error_if_missing_mode(self):
        functions.prompt.side_effect = [__file__, '']
        with self.assertRaises(ValueError):
            functions.add_object(self.repl)

    def test_add_object_raises_error_if_invalid_mode(self):
        functions.prompt.side_effect = [__file__, 'bad-mode']
        with self.assertRaises(ValueError):
            functions.add_object(self.repl)

    def test_can_remove_object_using_uid(self):
        functions.prompt.side_effect = ['1']
        self.repl.package.add_object(__file__, 'raw', {'target-device': '/'})
        self.assertEqual(len(self.repl.package), 1)
        functions.remove_object(self.repl)
        self.assertEqual(len(self.repl.package), 0)

    def test_can_remove_object_using_autocompleter_suggestion(self):
        functions.prompt.side_effect = ['1# {}'.format(__file__)]
        self.repl.package.add_object(__file__, 'raw', {'target-device': '/'})
        self.assertEqual(len(self.repl.package), 1)
        functions.remove_object(self.repl)
        self.assertEqual(len(self.repl.package), 0)

    def test_remove_object_raises_error_if_invalid_uid(self):
        functions.prompt.side_effect = ['invalid']
        with self.assertRaises(ValueError):
            functions.remove_object(self.repl)

    def test_can_edit_object(self):
        functions.prompt.side_effect = ['1', 'skip', '200']
        self.repl.package.add_object(__file__, 'raw', {
            'target-device': '/',
            'skip': 100,
        })
        obj = self.repl.package.objects[1]
        self.assertEqual(obj.options['skip'], 100)
        functions.edit_object(self.repl)
        obj = self.repl.package.objects[1]
        self.assertEqual(obj.options['skip'], 200)

    def test_edit_object_raises_error_if_invalid_uid(self):
        functions.prompt.side_effect = ['23']
        with self.assertRaises(ValueError):
            functions.edit_object(self.repl)

    def test_edit_object_raises_error_if_invalid_option(self):
        functions.prompt.side_effect = ['1', 'invalid']
        self.repl.package.add_object(__file__, 'raw', {'target-device': '/'})
        with self.assertRaises(ValueError):
            functions.edit_object(self.repl)

    def test_can_add_hardware_without_revision(self):
        functions.prompt.side_effect = ['PowerX', '']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 0)

    def test_can_add_hardware_with_revision(self):
        functions.prompt.side_effect = ['PowerX', 'rev.1']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 1)

    def test_can_add_multiple_hardwares_and_revisions(self):
        functions.prompt.side_effect = ['PowerX PowerY', 'PX1 PX2', 'PY1']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        hardware_1 = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware_1['revisions']), 2)
        hardware_2 = self.repl.package.supported_hardware['PowerY']
        self.assertEqual(len(hardware_2['revisions']), 1)

    def test_can_remove_supported_hardware(self):
        functions.prompt.side_effect = ['PowerX', '']
        self.repl.package.add_supported_hardware('PowerX')
        self.repl.package.add_supported_hardware('PowerY')
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertIsNone(self.repl.package.supported_hardware.get('PowerX'))

    def test_can_remove_many_supported_hardwares(self):
        functions.prompt.side_effect = ['PowerX PowerY', '', '']
        self.repl.package.add_supported_hardware('PowerX')
        self.repl.package.add_supported_hardware('PowerY')
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 0)

    def test_can_remove_only_one_hardware_revision(self):
        functions.prompt.side_effect = ['PowerX', '1']
        self.repl.package.add_supported_hardware(
            'PowerX', revisions=['1', '2'])
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertEqual(len(hardware['revisions']), 1)

    def test_can_remove_many_hardware_revisions(self):
        functions.prompt.side_effect = ['PowerX', '1 2']
        self.repl.package.add_supported_hardware(
            'PowerX', revisions=['1', '2'])
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertEqual(len(hardware['revisions']), 0)
