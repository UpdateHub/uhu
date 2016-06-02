# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest

from efu.upload import upload


class UploadTestCase(unittest.TestCase):

    def test_upload_raises_error_with_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            upload.upload_patch('invalid_file.txt')

    def test_upload_finishes(self):
        observed = upload.upload_patch(__file__)
        self.assertIsNone(observed)
