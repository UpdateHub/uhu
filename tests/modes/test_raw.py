# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from utils import UHUTestCase
from .base import ModeTestCaseMixin


class RawObjectTestCase(ModeTestCaseMixin, UHUTestCase):
    mode = 'raw'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'target-type': 'device',
            'target': '/dev/sda',
        }
        self.default_template = {
            'filename': self.fn,
            'mode': 'raw',
            'install-condition': 'always',
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'truncate': False
        }
        self.default_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'truncate': False,
        }

        self.full_options = {
            'filename': self.fn,
            'install-condition': 'always',
            'install-condition-pattern-type': None,
            'install-condition-pattern': None,
            'install-condition-seek': None,
            'install-condition-buffer-size': None,
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
        }
        self.full_template = {
            'filename': self.fn,
            'install-condition': 'always',
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
        }
        self.full_metadata = {
            'filename': self.fn,
            'size': self.size,
            'sha256sum': self.sha256sum,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
            'chunk-size': 1,
            'count': 2,
            'seek': 3,
            'skip': 4,
            'truncate': True,
        }
