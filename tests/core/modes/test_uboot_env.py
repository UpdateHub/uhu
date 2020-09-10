# Copyright (C) 2020 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from utils import UHUTestCase
from .base import ModeTestCaseMixin


class UbootEnvObjectTestCase(ModeTestCaseMixin, UHUTestCase):
    mode = 'uboot-env'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'mode': self.mode,
        }
        self.default_template = {
            'mode': 'uboot-env',
            'filename': self.fn,
        }
        self.default_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'uboot-env',
        }

        self.full_options = {
            'filename': self.fn,
            'mode': self.mode,
        }
        self.full_template = {
            'mode': 'uboot-env',
            'filename': self.fn,
        }
        self.full_metadata = {
            'filename': self.fn,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'mode': 'uboot-env',
        }
