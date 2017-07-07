# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from uhu.utils import CHUNK_SIZE_VAR

from utils import FileFixtureMixin, EnvironmentFixtureMixin, UHUTestCase


class PackageTestCase(FileFixtureMixin, EnvironmentFixtureMixin, UHUTestCase):

    def setUp(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        self.version = '2.0'
        self.product = 'a' * 64
        self.hardware = 'PowerX'
        self.pkg_uid = 'pkg-uid'
        self.obj_fn = self.create_file('spam', name='object')
        self.obj_options = {
            'filename': self.obj_fn,
            'mode': 'raw',
            'target-type': 'device',
            'target': '/dev/sda',
        }
