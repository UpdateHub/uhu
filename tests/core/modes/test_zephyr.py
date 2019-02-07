# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from utils import UHUTestCase
from .base import ModeTestCaseMixin


class ZephyrObjectTestCase(ModeTestCaseMixin, UHUTestCase):
    mode = 'zephyr'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'mode': self.mode,
        }
        self.default_template = {
            'filename': self.fn,
            'mode': 'zephyr',
        }
        self.default_metadata = {
            'filename': self.fn,
            'mode': 'zephyr',
            'sha256sum': self.sha256sum,
            'size': self.size,
        }

        self.full_options = {
            'filename': self.fn,
            'mode': self.mode,
        }
        self.full_template = {
            'filename': self.fn,
            'mode': 'zephyr',
        }
        self.full_metadata = {
            'filename': self.fn,
            'mode': 'zephyr',
            'sha256sum': self.sha256sum,
            'size': self.size,
        }
