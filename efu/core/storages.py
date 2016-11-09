# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import requests


def dummy_object_upload(obj, url, callback=None):
    from .object import ObjectReader
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
