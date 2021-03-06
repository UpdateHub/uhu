# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from utils import UHUTestCase
from .base import ModeTestCaseMixin


class ImxkobsObjectTestCase(ModeTestCaseMixin, UHUTestCase):
    mode = 'imxkobs'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'mode': self.mode,
        }
        self.default_template = {
            'filename': self.fn,
            'mode': 'imxkobs',
            'install-condition': 'always',
        }
        self.default_metadata = {
            'filename': self.fn,
            'size': self.size,
            'sha256sum': self.sha256sum,
            'mode': 'imxkobs',
        }

        self.full_options = {
            'filename': self.fn,
            'mode': self.mode,
            'install-condition': 'always',
            'install-condition-pattern-type': None,
            'install-condition-pattern': None,
            'install-condition-seek': None,
            'install-condition-buffer-size': None,
            '1k_padding': True,
            'search_exponent': 1,
            'chip_0_device_path': '/dev/mtd0',
            'chip_1_device_path': '/dev/mtd1',
        }
        self.full_template = {
            'filename': self.fn,
            'mode': 'imxkobs',
            'install-condition': 'always',
            '1k_padding': True,
            'search_exponent': 1,
            'chip_0_device_path': '/dev/mtd0',
            'chip_1_device_path': '/dev/mtd1',
        }
        self.full_metadata = {
            'filename': self.fn,
            'size': self.size,
            'sha256sum': self.sha256sum,
            'mode': 'imxkobs',
            '1k_padding': True,
            'search_exponent': 1,
            'chip_0_device_path': '/dev/mtd0',
            'chip_1_device_path': '/dev/mtd1',
        }
