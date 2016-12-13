# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

from progress.spinner import Spinner
from progress.bar import Bar


class BaseCallback:

    coeficient = 1

    def __init__(self):
        self.uploading = False
        self.total = 0
        self.parcel = 0

    def object_read(self, obj, full=False):
        n = len(obj) if full else 1
        for _ in range(n):
            self._object_read()

    def _object_read(self):
        if self.uploading:
            self.total += 1
            if (self.total % self.parcel) == 0:
                self.object_read_upload_callback()
        else:
            self.object_read_load_callback()

    def start_package_upload(self, objects):
        self.uploading = True
        total = sum(len(obj) for obj in objects)
        self.parcel = (total / 100) * self.coeficient
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
        self.progress = Bar('Uploading objects:', max=100, suffix=suffix)

    def finish_package_upload_callback(self):
        print('\033[1K\rUploading objects: ok\033[?25h')


class NoTTYCallback(BaseCallback):

    coeficient = 5

    def start_objects_load(self):
        print('Loading objects: ', end='', flush=True)

    def object_read_upload_callback(self):
        progress = int((self.total // self.parcel) * self.coeficient)
        print('{}% '.format(progress), end='', flush=True)

    def finish_objects_load(self):
        print('ok', flush=True)

    def start_package_upload_callback(self):
        print('Uploading objects:', flush=True)

    def finish_package_upload_callback(self):
        print()


def get_callback():
    if sys.stdout.isatty():
        return TTYCallback()
    return NoTTYCallback()
