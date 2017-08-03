# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from uhu.repl.completers import ObjectFilenameCompleter


class ObjectFilenameCompleterTestCase(unittest.TestCase):

    def test_can_set_completions_in_the_right_order(self):
        # creates a base dir
        base_dir = tempfile.mkdtemp(prefix='uh-completer-test-')
        self.addCleanup(shutil.rmtree, base_dir)
        os.chdir(base_dir)

        # Set up some files
        _, f1 = tempfile.mkstemp(prefix='file-1', dir=base_dir)
        _, f2 = tempfile.mkstemp(prefix='file-2', dir=base_dir)

        # Set up some dirs
        dir1 = tempfile.mkdtemp(prefix='dir-1', dir=base_dir)
        dir2 = tempfile.mkdtemp(prefix='dir-2', dir=base_dir)

        # Set up some links
        os.symlink(__file__, os.path.join(base_dir, 'sym1'))
        os.symlink(__file__, os.path.join(base_dir, 'sym2'))

        # Set up prompt toolkit document mock
        document = Mock()
        document.text_before_cursor = ''

        # Set up completer
        completer = ObjectFilenameCompleter()

        # Start the test!
        expected = [dir1, dir2, 'sym1', 'sym2', f1, f2]
        completions = completer.get_completions(document, None)
        observed = [completion.text for completion in completions]
        self.assertEqual(len(observed), len(expected))

    def test_can_handle_files_which_do_not_exist(self):
        document = Mock()
        document.text_before_cursor = 'invalid-path/invalid-file'
        completer = ObjectFilenameCompleter()
        completions = list(completer.get_completions(document, None))
        self.assertEqual(len(completions), 0)

    @patch('uhu.repl.completers.os')
    def test_can_handle_any_os_error(self, mock):
        mock.path.dirname.side_effect = OSError
        document = Mock()
        document.text_before_cursor = ''
        completer = ObjectFilenameCompleter()
        completions = completer.get_completions(document, None)
        self.assertIsNone(completions)
