# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import subprocess
import unittest
from distutils.spawn import find_executable


class CLITestCase(unittest.TestCase):

    def test_efu_is_a_cli_command(self):
        response = find_executable('efu')
        self.assertTrue(response)

    def test_efu_can_be_called_as_a_module(self):
        response = subprocess.call(['python', '-m', 'efu', '-h'])
        self.assertEqual(response, 0)

    def test_efu_is_parsing_arguments(self):
        response = subprocess.check_output(['efu', '-h'])
        self.assertIn('help', response.decode())

    def test_efu_raises_error_when_called_without_arguments(self):
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call('efu')


class UploadCommandTestCase(unittest.TestCase):

    def setUp(self):
        self.patch_file_name = '/tmp/patch.bin'
        open(self.patch_file_name, 'wb')

    def tearDown(self):
        os.remove(self.patch_file_name)

    def test_upload_command_exists(self):
        response = subprocess.check_output(['efu', 'upload', '-h'])
        self.assertIn('upload', response.decode())

    def test_upload_command_requires_a_valid_filename(self):
        # Checks if a filename is provided
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call(['efu', 'upload'])

        # Checks that a file must exists
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call(['efu', 'upload', 'no_exists.bin'])

        # Checks a valid file
        command = ['efu', 'upload', self.patch_file_name]
        response = subprocess.check_call(command)
        self.assertEqual(response, 0)
