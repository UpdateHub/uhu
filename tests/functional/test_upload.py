# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import json
import subprocess

from ..base import BaseTransactionTestCase


class UploadCommandTestCase(BaseTransactionTestCase):

    def test_upload_command_exists(self):
        response = subprocess.check_output(['efu', 'upload', '--help'])
        self.assertIn('upload', response.decode())

    def test_upload_command_requires_a_filename(self):
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call(['efu', 'upload'])

    def test_upload_command_requires_a_existent_filename(self):
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call(['efu', 'upload', 'no_exists.json'])

    def test_upload_command_runs_successfully(self):
        pkg = self.set_complete_transaction_response()
        command = ['efu', 'upload', pkg]
        response = subprocess.check_call(command)
        self.assertEqual(response, 0)
