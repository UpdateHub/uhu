# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from progress.spinner import Spinner
from progress.bar import Bar


class PushCallback:

    def __init__(self):
        self.progress = None
        self.parcel = 1
        self.total = 0

    def start_objects_load(self):
        self.progress = Spinner('Loading objects: ')

    def object_read(self):
        self.total += 1
        # updates only when parcel is reached
        if (self.total % self.parcel) != 0:
            return
        if self.progress is not None:
            self.progress.next()
        self.total = 0

    def finish_objects_load(self):
        self.progress.finish()
        print('\rLoading objects: ok')

    def start_package_upload(self, objects):
        total = sum(len(obj) for obj in objects)
        self.parcel = total / 100
        self.progress = Bar(
            'Uploading objects:', max=100,
            suffix='%(percent)d%% ETA: %(eta)ds')

    def finish_package_upload(self):
        print('\033[1K', end='')
        print('\rUploading objects: ok')

    def push_finish(self, pkg, response):
        if response.ok:
            print('Finished! Your package UID is {}'.format(pkg.uid))
        print('\033[?25h', end='')
