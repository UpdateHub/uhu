# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import re
import subprocess
from tempfile import mkstemp

from ..base import BasePushTestCase


class PushCommandTestCase(BasePushTestCase):

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
        pkg = self.fixture.set_push(1)
        command = ['efu', 'push', pkg]
        response = subprocess.check_call(command)
        self.assertEqual(response, 0)


class PushOutputTestCase(BasePushTestCase):

    def setUp(self):
        super().setUp()
        self.pattern = '/tmp/tmp.+? '
        self.fixture_dir = 'tests/functional/output_fixtures'
        _, self.stdout = mkstemp()
        self.addCleanup(os.remove, self.stdout)

    def get_fixture_output(self, fn):
        with open(os.path.join(self.fixture_dir, fn)) as fp:
            content = fp.read()
        return re.sub(self.pattern, '', content)

    def get_cmd_output(self, pkg):
        command = 'efu push {} > {}'.format(pkg, self.stdout)
        subprocess.call(command, shell=True)
        with open(self.stdout) as fp:
            content = fp.read()
        return re.sub(self.pattern, '', content)

    def test_success_output(self):
        pkg = self.fixture.set_push(1, file_size=5, success_files=2)
        expected = self.get_fixture_output('success')
        observed = self.get_cmd_output(pkg)
        self.assertEqual(expected, observed)

    def test_existent_files_output(self):
        pkg = self.fixture.set_push(
            1, file_size=5, existent_files=2, success_files=0)
        expected = self.get_fixture_output('existent_files')
        observed = self.get_cmd_output(pkg)
        self.assertEqual(expected, observed)

    def test_start_push_fail_output(self):
        pkg = self.fixture.set_push(
            1, file_size=5, start_success=False)
        expected = self.get_fixture_output('start_push_fail')
        observed = self.get_cmd_output(pkg)
        self.assertEqual(expected, observed)

    def test_finish_push_fail_output(self):
        pkg = self.fixture.set_push(
            1, file_size=5, finish_success=False)
        expected = self.get_fixture_output('finish_push_fail')
        observed = self.get_cmd_output(pkg)
        self.assertEqual(expected, observed)

    def test_part_file_fail_output(self):
        pkg = self.fixture.set_push(
            1, file_size=5, part_fail_files=2, success_files=0)
        expected = self.get_fixture_output('file_part_fail')
        observed = self.get_cmd_output(pkg)
        self.assertEqual(expected, observed)

    def test_mixed_output(self):
        pkg = self.fixture.set_push(
            1, file_size=5, success_files=1,
            part_fail_files=1, existent_files=1)
        expected = self.get_fixture_output('mixed')
        observed = self.get_cmd_output(pkg)
        self.assertEqual(expected, observed)
