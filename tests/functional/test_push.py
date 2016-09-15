# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import re
import subprocess

from ..base import PushMockMixin, BaseTestCase


class PushCommandTestCase(PushMockMixin, BaseTestCase):

    def test_push_command_exists(self):
        cmd = ['efu', 'package', 'push', '--help']
        response = subprocess.check_output(cmd)
        self.assertIn('push', response.decode())

    def test_push_command_runs_successfully(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product, uploads=uploads)
        command = ['efu', 'package', 'push', '2.0']
        response = subprocess.check_call(command)
        self.assertEqual(response, 0)


class PushOutputTestCase(PushMockMixin, BaseTestCase):

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
        command = 'efu package push {} > {}'.format(self.version, self.stdout)

        subprocess.call(command, shell=True)
        with open(self.stdout) as fp:
            content = fp.read()
        return re.sub(self.pattern, '', content)

    def test_success_output(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product, uploads=uploads)
        expected = self.get_fixture_output('success')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_existent_files_output(self):
        uploads = self.create_uploads_meta(self.files, file_exists=True)
        self.set_push(self.product, uploads=uploads)
        expected = self.get_fixture_output('existent_files')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_start_push_fail_output(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(self.product, uploads=uploads, start_success=False)
        expected = self.get_fixture_output('start_push_fail')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_finish_push_fail_output(self):
        uploads = self.create_uploads_meta(self.files)
        self.set_push(
            self.product, uploads=uploads, finish_success=False)
        expected = self.get_fixture_output('finish_push_fail')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)

    def test_file_part_fail_output(self):
        uploads = self.create_uploads_meta(self.files, success=False)
        self.set_push(self.product, uploads=uploads)

        expected = self.get_fixture_output('file_part_fail')
        observed = self.get_cmd_output()
        self.assertEqual(expected, observed)
