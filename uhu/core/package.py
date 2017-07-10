# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import json

import requests
from pkgschema import validate_metadata

from ..exceptions import DownloadError, UploadError
from ..http.request import Request, format_server_error
from ..utils import call, get_server_url

from .hardware import SupportedHardwareManager
from .objects import ObjectsManager
from .upload import ObjectUploadResult


MODES = ['single', 'active-inactive']


class Package:
    """A package represents a group of objects."""

    def __init__(self, version=None, product=None, dump=None):
        if dump is None:
            self.version = version
            self.product = product
            self.objects = ObjectsManager()
            self.supported_hardware = SupportedHardwareManager()
        else:
            self.version = dump.get('version')  # TODO: validate it
            self.product = dump.get('product')  # TODO: validate it
            self.objects = ObjectsManager(dump=dump)
            self.supported_hardware = SupportedHardwareManager(dump=dump)
        self.uid = None

    def to_metadata(self):
        """Serialize package as metadata."""
        metadata = {
            'product': self.product,
            'version': self.version,
        }
        metadata.update(self.objects.to_metadata())
        metadata.update(self.supported_hardware.to_metadata())
        return metadata

    def to_template(self, with_version=True):
        """Serialize package to dump to a file."""
        template = {'product': self.product}
        template['version'] = self.version if with_version else None
        template.update(self.objects.to_template())
        template.update(self.supported_hardware.to_template())
        return template

    def upload_metadata(self):
        metadata = self.to_metadata()
        validate_metadata(metadata)
        payload = json.dumps(metadata)
        url = get_server_url('/packages')
        response = Request(
            url, method='POST', payload=payload, json=True).send()
        if response.status_code == 401:
            err = ('You are not authorized to push. '
                   'Did you set your credentials?')
            raise UploadError(err)
        response_body = response.json()
        if response.status_code != 201:
            error_msg = format_server_error(response_body)
            raise UploadError(error_msg.format(error_msg))
        self.uid = response_body['uid']

    def upload_objects(self, callback=None):
        results = []
        objects = self.objects[0]  # this means first installation set
        call(callback, 'start_package_upload', objects)
        for obj in objects:
            results.append(obj.upload(self.uid, callback))
        call(callback, 'finish_package_upload')
        for result in results:
            if not ObjectUploadResult.is_ok(result):
                err = 'Some objects has not been fully uploaded'
                raise UploadError(err)

    def finish_push(self, callback=None):
        url = get_server_url('/packages/{}/finish'.format(self.uid))
        response = Request(url, 'PUT').send()
        if response.status_code != 204:
            raise UploadError('Push failed\n{}'.format(response.text))
        call(callback, 'push_finish', self.uid)

    def push(self, callback=None):
        self.upload_metadata()
        self.upload_objects(callback)
        self.finish_push(callback)

    @classmethod
    def download_metadata(cls, uid):
        path = '/packages/{}'.format(uid)
        try:
            response = Request(get_server_url(path), 'GET').send()
        except requests.exceptions.ConnectionError:
            raise DownloadError('Can\'t reach server.')
        if response.ok:
            return response.json()
        raise DownloadError(response.text)

    def download_objects(self, uid):
        for obj in self.get_download_list():
            path = '/packages/{}/objects/{}'.format(uid, obj['sha256sum'])
            url = get_server_url(path)
            obj.download(url)

    def get_download_list(self):
        """Returns a list with all objects that must be downloaded.

        If local object exists and it is equal to remote object, we
        do not downloaded it.  Verifies if local files will not be
        overwritten by incoming files.

        If local objects exists and it is different from remote
        object, we raise an exception to avoid object overwritting.
        """
        objects = []
        for obj in self.objects.all():
            if not obj.exists:
                objects.append(obj)
                continue  # File does not exist, must be downloaded
            sha256sum = hashlib.sha256()
            for chunk in obj:
                sha256sum.update(chunk)
            if sha256sum.hexdigest() != obj['sha256sum']:
                # Local object diverges from server object, must abort
                raise DownloadError(
                    '{} will be overwritten'.format(obj.filename))
            # If we got here, means that object exists locally and
            # is equal to remote object. Therefore, it must be not
            # downloaded.
        return objects

    @classmethod
    def get_status(cls, uid):
        url = get_server_url('/packages/{}'.format(uid))
        response = Request(url, 'GET', json=True).send()
        if response.status_code != 200:
            raise ValueError('Status not found')
        return response.json().get('status')

    def __str__(self):
        return '\n'.join([
            'Product: {}'.format(self.product),
            'Version: {}'.format(self.version),
            str(self.supported_hardware),
            str(self.objects),
        ])
