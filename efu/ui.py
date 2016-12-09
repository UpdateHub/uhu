# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from progress.spinner import Spinner
from progress.bar import Bar


class PushCallback:

    def __init__(self):
        self.progress = None
        self.spinner = None

    def start_objects_load(self):
        self.spinner = Spinner('Loading objects: ')

    def object_read(self):
        if self.progress is not None:
            self.progress.next()
        if self.spinner is not None:
            self.spinner.next()

    def finish_objects_load(self):
        self.spinner.finish()
        print('\rLoading objects: ok')

    def start_package_upload(self, objects):
        self.spinner = None
        total = sum(len(obj) for obj in objects)
        self.progress = Bar(
            'Uploading objects:', max=total,
            suffix='%(percent)d%% ETA: %(eta)ds')

    def finish_package_upload(self):
        print('\033[1K', end='')
        print('\rUploading objects: ok')

    def push_finish(self, pkg, response):
        if response.ok:
            print('Finished! Your package UID is {}'.format(pkg.uid))
        print('\033[?25h', end='')
