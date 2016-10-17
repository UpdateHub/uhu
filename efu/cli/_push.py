# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from math import ceil

from progress.bar import Bar

from ..core.object import ObjectUploadResult


GREEN = '\033[92m'
RED = '\033[91m'
END = '\033[0m'

SUCCESS_MSG = '{}SUCCESS{}'.format(GREEN, END)
FAIL_MSG = '{}FAIL{}'.format(RED, END)


class PushCallback:

    def __init__(self):
        self.object_bar = None

    def pre_package_load(self, package):  # pylint: disable=W0613
        print('Start Reading package')

    def package_load(self, package):  # pylint: disable=W0613
        pass

    def post_package_load(self, package):  # pylint: disable=W0613
        print('Finish reading package')

    def pre_object_load(self, obj):
        size = ceil(obj.size / obj.chunk_size)
        self.object_bar = Bar(obj.filename, max=size)

    def object_load(self, obj):  # pylint: disable=W0613
        self.object_bar.next()

    def post_object_load(self, obj):  # pylint: disable=W0613
        self.object_bar.finish()

    def pre_object_upload(self, obj):
        self.object_bar = Bar(obj.filename, max=len(obj))

    def object_upload(self, obj):  # pylint: disable=W0613
        self.object_bar.next()

    def post_object_upload(self, obj, status):
        if status == ObjectUploadResult.EXISTS:
            print(obj.filename, 'already uploaded', flush=True, end='')
        self.object_bar.finish()

    def push_start(self, response):
        print('Starting push: ', end='')
        if response.ok:
            print(SUCCESS_MSG)
        else:
            print(FAIL_MSG)

    def push_finish(self, pkg, response):
        print('Finishing push: ', end='')
        if response.ok:
            print(SUCCESS_MSG)
            print('Package UID: {}'.format(pkg.uid))
        else:
            print(FAIL_MSG)
