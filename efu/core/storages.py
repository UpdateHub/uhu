# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import requests

from ..utils import call


class BaseStorageBackend:

    def __init__(self, obj, callback=None):
        self.object = obj
        self.success = False
        self.callback = callback

    def _upload(self):
        for chunk in self.object:
            call(self.callback, 'object_upload', self.object)
            yield chunk

    def upload(self, url):
        response = requests.put(url, data=self._upload())
        if response.ok:
            self.success = True


class SwiftStorageBackend(BaseStorageBackend):
    pass


STORAGES = {
    'dummy': BaseStorageBackend,
    'swift': SwiftStorageBackend
}
