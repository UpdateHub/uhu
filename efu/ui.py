# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from progress.spinner import Spinner
from progress.bar import Bar

from .core.object import ObjectUploadResult


class PushCallback:

    def __init__(self):
        self.progress = None
        self.spinner = None

    def start_objects_load(self):
        self.spinner = Spinner('Loading objects: ')

    def finish_objects_load(self):
        self.spinner.finish()
        print('\rLoading objects: ok')

    def object_read(self):
        if self.progress is not None:
            self.progress.next()
        if self.spinner is not None:
            self.spinner.next()

    def start_object_upload(self, obj):
        self.spinner = None
        self.progress = Bar(
            obj.filename, max=len(obj), suffix='%(percent)d%% ETA: %(eta)ds')

    def finish_object_upload(self, obj, status):
        if status == ObjectUploadResult.EXISTS:
            print(obj.filename, 'already uploaded', flush=True, end='')
        self.progress.finish()

    def push_start(self, response):
        print('Uploading objects: ', end='')
        if response.ok:
            print()
        else:
            print('failed.')

    def push_finish(self, pkg, response):
        if response.ok:
            print('Package UID: {}'.format(pkg.uid))
            print('Finished!')
