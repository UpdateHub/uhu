# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os
from enum import Enum

from pkgschema import validate_metadata, ValidationError

from .. import http
from ..exceptions import UploadError
from ..utils import call, get_server_url, get_chunk_size


# Utilities

class ObjectReader:  # pylint: disable=too-few-public-methods
    """Read-only object class. Used when uploading with requests."""

    def __init__(self, filename, callback=None):
        self.filename = os.path.realpath(filename)
        self.callback = callback

    def __len__(self):
        return os.path.getsize(self.filename)

    def __iter__(self):
        """Yields every single chunk."""
        chunk_size = get_chunk_size()
        with open(self.filename, 'br') as fp:
            for chunk in iter(lambda: fp.read(chunk_size), b''):
                yield chunk
                call(self.callback, 'object_read')


def dummy_object_upload(filename, url, callback=None):
    data = ObjectReader(filename, callback)
    response = http.put(url, data=data, sign=False)
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


class ObjectUploadResult(Enum):
    SUCCESS = 1
    EXISTS = 2
    FAIL = 3

    @classmethod
    def is_ok(cls, result):
        return result in (cls.SUCCESS, cls.EXISTS)


# Push Package

def push_package(metadata, objects, callback=None):
    package_uid = upload_metadata(metadata)
    upload_objects(package_uid, objects, callback)
    finish_package(package_uid, callback)
    return package_uid


def upload_metadata(metadata):
    try:
        validate_metadata(metadata)
    except ValidationError:
        raise UploadError('You have an invalid package metadata.')
    url = get_server_url('/packages')
    payload = json.dumps(metadata)
    response = http.post(url, payload=payload, json=True)
    if response.status_code == 401:
        err = ('You are not authorized to push. '
               'Did you set your credentials?')
        raise UploadError(err)
    response_body = response.json()
    if response.status_code != 201:
        raise UploadError(http.format_server_error(response_body))
    return response_body['uid']


def upload_object(obj, package_uid, callback=None):
    """Uploads a package object to UpdateHub server."""
    # First, check if we can upload the object
    url = get_server_url('/packages/{}/objects/{}'.format(
        package_uid, obj['sha256sum']))
    body = json.dumps({'etag': obj['md5']})
    response = http.post(url, body, json=True)
    if response.status_code == 200:  # Object already uploaded
        result = ObjectUploadResult.EXISTS
        call(callback, 'object_read', obj['chunks'])
    elif response.status_code == 201:  # Object must be uploaded
        body = response.json()
        upload = STORAGES[body['storage']]
        success = upload(obj['filename'], body['url'], callback)
        if success:
            result = ObjectUploadResult.SUCCESS
        else:
            result = ObjectUploadResult.FAIL
    else:  # It was not possible to check if we can upload
        raise UploadError(http.format_server_error(response.json()))
    return result


def upload_objects(package_uid, objects, callback=None):
    call(callback, 'start_package_upload', objects)
    results = [upload_object(obj, package_uid, callback) for obj in objects]
    call(callback, 'finish_package_upload')
    for result in results:
        if not ObjectUploadResult.is_ok(result):
            raise UploadError('Some objects has not been fully uploaded')


def finish_package(package_uid, callback=None):
    url = get_server_url('/packages/{}/finish'.format(package_uid))
    response = http.put(url)
    if response.status_code != 204:
        raise UploadError('Push failed\n{}'.format(response.text))
    call(callback, 'push_finish', package_uid)


# Package status

def get_package_status(package_uid):
    url = get_server_url('/packages/{}'.format(package_uid))
    response = http.get(url, json=True)
    if response.status_code != 200:
        raise ValueError('Status not found')
    return response.json().get('status')