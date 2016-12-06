# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from efu.utils import CHUNK_SIZE_VAR

from utils import FileFixtureMixin, EnvironmentFixtureMixin, EFUTestCase


class PackageTestCase(FileFixtureMixin, EnvironmentFixtureMixin, EFUTestCase):

    def setUp(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        self.version = '2.0'
        self.product = '1234'
        self.hardware = 'PowerX'
        self.hardware_revision = ['PX230']
        self.supported_hardware = {
            self.hardware: {
                'name': self.hardware,
                'revisions': self.hardware_revision,
            }
        }
        self.pkg_uid = 'pkg-uid'
        self.obj_content = b'spam'
        self.obj_fn = self.create_file(self.obj_content)
        self.obj_sha256 = self.sha256sum(self.obj_content)
        self.obj_mode = 'raw'
        self.obj_options = {'target-device': '/dev/sda'}
        self.obj_size = 4
