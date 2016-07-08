# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import re
import subprocess

from ..base import EFUTestCase


class PushCommandTestCase(EFUTestCase):

    def test_push_command_exists(self):
        response = subprocess.check_output(['efu', 'push', '--help'])
        self.assertIn('push', response.decode())

    def test_push_command_requires_a_filename(self):
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call(['efu', 'push'])

    def test_push_command_requires_a_existent_filename(self):
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_call(['efu', 'push', 'no_exists.json'])

    def test_push_command_runs_successfully(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product_id, uploads=uploads)
        command = ['efu', 'push', self.package_fn]
        response = subprocess.check_call(command)
        self.assertEqual(response, 0)


class PushOutputTestCase(EFUTestCase):

    def setUp(self):
        super().setUp()
        self.pattern = '/tmp/tmp.+? '
        self.fixture_dir = 'tests/functional/output_fixtures'
        self.stdout = self.create_file(b'')

    def get_fixture_output(self, fn):
        with open(os.path.join(self.fixture_dir, fn)) as fp:
            content = fp.read()
        return re.sub(self.pattern, '', content)

    def get_cmd_output(self):
        command = 'efu push {} > {}'.format(self.package_fn, self.stdout)

        subprocess.call(command, shell=True)
        with open(self.stdout) as fp:
            content = fp.read()
        return re.sub(self.pattern, '', content)

    def test_success_output(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product_id, uploads=uploads)

        expected = self.get_fixture_output('success')
        observed = self.get_cmd_output()

        print(observed)
        self.assertEqual(expected, observed)

    def test_existent_files_output(self):
        uploads = self.create_uploads_meta(self.files, file_exists=True)
        self.set_push(self.product_id, uploads=uploads)

        expected = self.get_fixture_output('existent_files')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_start_push_fail_output(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product_id, uploads=uploads, start_success=False)
        expected = self.get_fixture_output('start_push_fail')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_finish_push_fail_output(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(
            self.product_id, uploads=uploads, finish_success=False)
        expected = self.get_fixture_output('finish_push_fail')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_file_part_fail_output(self):
        uploads = self.create_uploads_meta(self.files, success=False)
        self.set_push(self.product_id, uploads=uploads)

        expected = self.get_fixture_output('file_part_fail')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_mixed_output(self):
        f1, f2, f3 = self.files
        u1 = self.create_upload_meta(f1)
        u2 = self.create_upload_meta(f2, success=False)
        u3 = self.create_upload_meta(f3, file_exists=True)
        uploads = [u1, u2, u3]
        self.set_push(self.product_id, uploads=uploads)

        expected = self.get_fixture_output('mixed')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)
