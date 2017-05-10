# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import math
import sys

from progress.spinner import Spinner
from progress.bar import Bar


class BaseCallback:

    def __init__(self):
        self.uploading = False
        self.max = None

    def object_read(self, obj, full=False):
        n = len(obj) if full else 1
        for _ in range(n):
            self._object_read()

    def _object_read(self):
        if self.uploading:
            self.object_read_upload_callback()
        else:
            self.object_read_load_callback()

    def start_package_upload(self, objects):
        self.uploading = True
        self.max = sum(len(obj) for obj in objects)
        self.start_package_upload_callback()

    def finish_package_upload(self):
        self.uploading = False
        self.finish_package_upload_callback()

    def push_finish(self, uid):
        print('Finished! Your package UID is {}'.format(uid))

    def object_read_load_callback(self):
        pass

    def object_read_upload_callback(self):
        pass

    def start_package_upload_callback(self):
        pass

    def finish_package_upload_callback(self):
        pass


class TTYCallback(BaseCallback):

    def __init__(self):
        super().__init__()
        self.progress = None

    def start_objects_load(self):
        self.progress = Spinner('Loading objects: ')

    def object_read_load_callback(self):
        self.progress.next()

    def object_read_upload_callback(self):
        self.progress.next()

    def finish_objects_load(self):
        self.progress.finish()
        print('\rLoading objects: ok')

    def start_package_upload_callback(self):
        suffix = '%(percent)d%% ETA: %(eta)ds'
        self.progress = Bar('Uploading objects:', max=self.max, suffix=suffix)

    def finish_package_upload_callback(self):
        print('\033[1K\rUploading objects: ok\033[?25h')


class NoTTYCallback(BaseCallback):

    def __init__(self):
        super().__init__()
        self.current = 0
        self.coeficient = 5
        self.next_step = 0

    def start_objects_load(self):
        print('Loading objects: ', end='', flush=True)

    def object_read_upload_callback(self):
        self.current += 1
        progress = math.floor((self.current / self.max) * 100)
        if progress >= self.next_step:
            steps = progress // self.coeficient
            until = steps * self.coeficient
            for step in range(self.next_step, until, self.coeficient):
                print('{}% '.format(step), end='', flush=True)
            self.next_step = until

    def finish_objects_load(self):
        print('ok', flush=True)

    def start_package_upload_callback(self):
        print('Uploading objects:', flush=True)

    def finish_package_upload_callback(self):
        print('100%', flush=True)


def get_callback():
    if sys.stdout.isatty():
        return TTYCallback()
    return NoTTYCallback()
