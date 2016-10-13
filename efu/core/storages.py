# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import requests


class BaseStorageBackend:

    def __init__(self):
        self.success = False

    def upload(self, fn, url):
        with open(fn, 'rb') as fp:
            response = requests.put(url, data=fp)
        if response.ok:
            self.success = True


class SwiftStorageBackend(BaseStorageBackend):
    pass


STORAGES = {
    'dummy': BaseStorageBackend,
    'swift': SwiftStorageBackend
}
