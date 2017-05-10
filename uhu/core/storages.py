# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import os

import requests

from ..utils import call


class ObjectReader:
    """Read-only object class. Used when uploading with requests."""

    def __init__(self, obj, callback=None):
        self.obj = obj
        self.callback = callback

    def __len__(self):
        return os.path.getsize(self.obj.filename)

    def __iter__(self):
        for chunk in self.obj:
            call(self.callback, 'object_read', self.obj)
            yield chunk


def dummy_object_upload(obj, url, callback=None):
    data = ObjectReader(obj, callback)
    response = requests.put(url, data=data)
    return response.ok


def swift_object_upload(*args, **kw):
    return dummy_object_upload(*args, **kw)


def s3_object_upload(*args, **kw):
    return dummy_object_upload(*args, **kw)


STORAGES = {
    'dummy': dummy_object_upload,
    'swift': swift_object_upload,
    's3': s3_object_upload,
}
