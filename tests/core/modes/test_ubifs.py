# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from utils import UHUTestCase
from .base import ModeTestCaseMixin


class UBIFSObjectTestCase(ModeTestCaseMixin, UHUTestCase):
    mode = 'ubifs'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'mode': self.mode,
            'target-type': 'ubivolume',
            'target': 'system0'
        }
        self.default_template = {
            'mode': 'ubifs',
            'filename': self.fn,
            'target-type': 'ubivolume',
            'target': 'system0',
        }
        self.default_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'ubifs',
            'target-type': 'ubivolume',
            'target': 'system0'
        }

        self.full_options = {
            'filename': self.fn,
            'mode': self.mode,
            'target-type': 'ubivolume',
            'target': 'system0'
        }
        self.full_template = {
            'mode': 'ubifs',
            'filename': self.fn,
            'target-type': 'ubivolume',
            'target': 'system0',
        }
        self.full_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'ubifs',
            'target-type': 'ubivolume',
            'target': 'system0'
        }
