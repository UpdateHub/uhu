# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
import os
from enum import Enum

from pkgschema import validate_metadata, ValidationError

from uhu.config import config
from uhu.utils import call, get_server_url, get_chunk_size, sign_dict
from . import http


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
    try:
        http.put(url, data=data, sign=False)
        return ObjectUploadResult.SUCCESS
    except http.HTTPError:
        return ObjectUploadResult.FAIL


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


class UpdateHubError(Exception):
    """Exception to be used when API is broken."""


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
        raise UpdateHubError('You have an invalid package metadata.')
    url = get_server_url('/packages')
    signature = sign_dict(metadata, config.get_private_key_path())
    payload = json.dumps(metadata, sort_keys=True)
    headers = {'UH-SIGNATURE': signature}
    try:
        response = http.post(
            url, payload=payload, json=True, headers=headers).json()
        return response['uid']
    except http.HTTPError as error:
        raise UpdateHubError('Could not upload metadata: {}'.format(error))
    except (ValueError, KeyError):
        raise UpdateHubError('Could not upload metadata: unknown error.')


def upload_object(obj, package_uid, callback=None):
    """Uploads a package object to UpdateHub server."""
    # First, check if we should upload the object
    url = get_server_url('/packages/{}/objects/{}'.format(
        package_uid, obj['sha256sum']))
    body = json.dumps({'etag': obj['md5']})
    try:
        response = http.post(url, body, json=True)
    except http.HTTPError:
        return ObjectUploadResult.FAIL

    # Object already uploaded, return EXISTS.
    if response.status_code == 200:
        call(callback, 'object_read', obj['chunks'])
        return ObjectUploadResult.EXISTS

    # Object not uploaded, try to uploaded it.
    try:
        body = response.json()
        uploader = STORAGES[body['storage']]
        url = body['url']
    except (ValueError, KeyError):
        return ObjectUploadResult.FAIL
    return uploader(obj['filename'], url, callback)


def upload_objects(package_uid, objects, callback=None):
    call(callback, 'start_package_upload', objects)
    results = [upload_object(obj, package_uid, callback) for obj in objects]
    call(callback, 'finish_package_upload')
    if ObjectUploadResult.FAIL in results:
        raise UpdateHubError(
            'Some objects has not been fully uploaded. Try again later.')


def finish_package(package_uid, callback=None):
    url = get_server_url('/packages/{}/finish'.format(package_uid))
    try:
        http.put(url)
    except http.HTTPError as error:
        raise UpdateHubError(
            'Could not finish package on server: {}'.format(error))
    finally:
        call(callback, 'push_finish', package_uid)


# Package status

def get_package_status(package_uid):
    url = get_server_url('/packages/{}'.format(package_uid))
    try:
        return http.get(url, json=True).json()['status']
    except http.HTTPError as error:
        raise UpdateHubError(error)
    except (ValueError, KeyError):
        raise UpdateHubError('Could not get package info. Try again later.')
