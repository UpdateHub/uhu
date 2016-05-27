# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import subprocess
import unittest


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
