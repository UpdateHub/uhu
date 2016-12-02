# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from efu.repl.repl import EFURepl
from efu.repl import functions


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = EFURepl()


class PackageTestCase(BaseTestCase):

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


class ObjectManagementTestCase(BaseTestCase):

    @patch('efu.repl.helpers.prompt')
    def test_can_add_object(self, prompt):
        values = [__file__, 'copy', '', '/', '/', 'ext4', '', '', '']
        prompt.side_effect = values
        self.assertEqual(len(self.repl.package.objects.all()), 0)
        functions.add_object(self.repl)
        self.assertEqual(len(self.repl.package.objects.all()), 2)

    @patch('efu.repl.helpers.prompt')
    def test_can_remove_object_using_uid(self, prompt):
        prompt.side_effect = ['0']
        self.repl.package.objects.create(
            __file__, 'raw', {'target-device': '/'})
        self.assertEqual(len(self.repl.package.objects.all()), 2)
        functions.remove_object(self.repl)
        self.assertEqual(len(self.repl.package.objects.all()), 0)

    @patch('efu.repl.helpers.prompt')
    def test_can_remove_object_using_autocompleter_suggestion(self, prompt):
        prompt.side_effect = ['0# {}'.format(__file__)]
        self.repl.package.objects.create(
            __file__, 'raw', {'target-device': '/'})
        self.assertEqual(len(self.repl.package.objects.all()), 2)
        functions.remove_object(self.repl)
        self.assertEqual(len(self.repl.package.objects.all()), 0)

    @patch('efu.repl.helpers.prompt')
    def test_remove_object_raises_error_if_invalid_uid(self, prompt):
        prompt.side_effect = ['invalid']
        with self.assertRaises(ValueError):
            functions.remove_object(self.repl)

    @patch('efu.repl.helpers.prompt')
    def test_can_edit_object(self, prompt):
        prompt.side_effect = ['0', '0', 'count', '200']
        self.repl.package.objects.create(__file__, 'raw', {
            'target-device': '/',
            'count': 100,
        })
        obj = self.repl.package.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.options['count'], 100)
        functions.edit_object(self.repl)
        obj = self.repl.package.objects.get(index=0, installation_set=0)
        self.assertEqual(obj.options['count'], 200)

    @patch('efu.repl.helpers.prompt')
    def test_can_edit_object_filename(self, prompt):
        for i in range(2):
            self.repl.package.objects.create(
                __file__, 'raw', {'target-device': '/'})
        with tempfile.NamedTemporaryFile() as fp:
            prompt.side_effect = ['1', '0', 'filename', fp.name]
            obj = self.repl.package.objects.get(index=0, installation_set=1)
            self.assertEqual(obj.filename, __file__)
            functions.edit_object(self.repl)
            self.assertEqual(obj.filename, fp.name)

    @patch('efu.repl.helpers.prompt')
    def test_edit_object_raises_error_if_invalid_uid(self, prompt):
        prompt.side_effect = ['23']
        with self.assertRaises(ValueError):
            functions.edit_object(self.repl)

    @patch('efu.repl.helpers.prompt')
    def test_edit_object_raises_error_if_invalid_option(self, prompt):
        prompt.side_effect = ['1', 'invalid']
        self.repl.package.objects.create(
            __file__, 'raw', {'target-device': '/'})
        with self.assertRaises(ValueError):
            functions.edit_object(self.repl)


class HardwareManagementTestCase(BaseTestCase):

    @patch('efu.repl.functions.prompt')
    def test_can_add_hardware_without_revision(self, prompt):
        prompt.side_effect = ['PowerX', '']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 0)

    @patch('efu.repl.functions.prompt')
    def test_can_add_hardware_with_revision(self, prompt):
        functions.prompt.side_effect = ['PowerX', 'rev.1']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 1)

    @patch('efu.repl.functions.prompt')
    def test_can_add_multiple_hardwares_and_revisions(self, prompt):
        functions.prompt.side_effect = ['PowerX PowerY', 'PX1 PX2', 'PY1']
        self.assertEqual(len(self.repl.package.supported_hardware), 0)
        functions.add_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        hardware_1 = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware_1['revisions']), 2)
        hardware_2 = self.repl.package.supported_hardware['PowerY']
        self.assertEqual(len(hardware_2['revisions']), 1)

    @patch('efu.repl.functions.prompt')
    def test_can_remove_supported_hardware(self, prompt):
        functions.prompt.side_effect = ['PowerX', '']
        self.repl.package.add_supported_hardware('PowerX')
        self.repl.package.add_supported_hardware('PowerY')
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertIsNone(self.repl.package.supported_hardware.get('PowerX'))

    @patch('efu.repl.functions.prompt')
    def test_can_remove_many_supported_hardwares(self, prompt):
        functions.prompt.side_effect = ['PowerX PowerY', '', '']
        self.repl.package.add_supported_hardware('PowerX')
        self.repl.package.add_supported_hardware('PowerY')
        self.assertEqual(len(self.repl.package.supported_hardware), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 0)

    @patch('efu.repl.functions.prompt')
    def test_can_remove_only_one_hardware_revision(self, prompt):
        functions.prompt.side_effect = ['PowerX', '1']
        self.repl.package.add_supported_hardware(
            'PowerX', revisions=['1', '2'])
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertEqual(len(hardware['revisions']), 1)

    @patch('efu.repl.functions.prompt')
    def test_can_remove_many_hardware_revisions(self, prompt):
        functions.prompt.side_effect = ['PowerX', '1 2']
        self.repl.package.add_supported_hardware(
            'PowerX', revisions=['1', '2'])
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        hardware = self.repl.package.supported_hardware['PowerX']
        self.assertEqual(len(hardware['revisions']), 2)
        functions.remove_hardware(self.repl)
        self.assertEqual(len(self.repl.package.supported_hardware), 1)
        self.assertEqual(len(hardware['revisions']), 0)
