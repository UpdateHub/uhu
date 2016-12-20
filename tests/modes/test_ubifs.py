# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from utils import EFUTestCase
from .base import ModeTestCaseMixin


class UBIFSObjectTestCase(ModeTestCaseMixin, EFUTestCase):
    mode = 'ubifs'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'volume': 'system0'
        }
        self.default_template = {
            'mode': 'ubifs',
            'filename': self.fn,
            'volume': 'system0',
        }
        self.default_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'ubifs',
            'volume': 'system0'
        }

        self.full_options = {
            'filename': self.fn,
            'volume': 'system0'
        }
        self.full_template = {
            'mode': 'ubifs',
            'filename': self.fn,
            'volume': 'system0',
        }
        self.full_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'ubifs',
            'volume': 'system0'
        }
