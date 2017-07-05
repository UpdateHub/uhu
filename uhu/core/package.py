# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import json
from collections import OrderedDict

import requests
from pkgschema import validate_metadata

from ..exceptions import DownloadError, UploadError
from ..http.request import Request
from ..utils import call, get_server_url

from .hardware import SupportedHardwareManager
from .objects import ObjectsManager
from .upload import ObjectUploadResult


MODES = ['single', 'active-inactive']


def write_json(obj, fn):
    """Saves an obj as JSON into fn in an opnionated way."""
    with open(fn, 'w') as fp:
        json.dump(obj, fp, indent=4, sort_keys=True)
        fp.write('\n')


class Package:
    """A package represents a group of objects."""

    def __init__(self, mode, version=None, product=None):
        self.mode = mode
        self.uid = None
        self.version = version
        self.product = product
        self.objects = ObjectsManager(self.mode)
        self.supported_hardware = SupportedHardwareManager()

    @classmethod
    def from_file(cls, fn):
        """Creates a package from a dumped package."""
        with open(fn) as fp:
            dump = json.load(fp, object_pairs_hook=OrderedDict)
        return cls._from_dump(dump, 'from_file')

    @classmethod
    def from_metadata(cls, metadata):
        """Creates a package from a metadata object."""
        return cls._from_dump(metadata, 'from_metadata')

    @classmethod
    def _from_dump(cls, dump, constructor):
        objects_constructor = getattr(ObjectsManager, constructor)
        objects = objects_constructor(dump)
        package = Package(
            mode=objects.mode,
            version=dump.get('version'),
            product=dump.get('product'))
        package.objects = objects
        hardware_constructor = getattr(SupportedHardwareManager, constructor)
        package.supported_hardware = hardware_constructor(dump)
        return package

    def to_metadata(self):
        """Serialize package as metadata."""
        metadata = {
            'product': self.product,
            'version': self.version,
        }
        metadata.update(self.objects.to_metadata())
        metadata.update(self.supported_hardware.to_metadata())
        return metadata

    def to_template(self):
        """Serialize package to dump to a file."""
        template = {
            'version': self.version,
            'product': self.product,
        }
        template.update(self.objects.to_template())
        template.update(self.supported_hardware.to_template())
        return template

    def export(self, dest):
        """Writes package template in dest file (without version)."""
        template = self.to_template()
        template['version'] = None
        write_json(template, dest)

    def dump(self, dest):
        """Writes package template in dest file (with version)."""
        write_json(self.to_template(), dest)

    def upload_metadata(self):
        metadata = self.to_metadata()
        validate_metadata(metadata)
        payload = json.dumps(metadata)
        url = get_server_url('/packages')
        response = Request(
            url, method='POST', payload=payload, json=True).send()
        response_body = response.json()
        if response.status_code != 201:
            errors = '\n'.join(response_body.get('errors', []))
            error_msg = 'It was not possible to start pushing:\n{}'
            raise UploadError(error_msg.format(errors))
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
        response = Request(self.get_finish_push_url(), 'PUT').send()
        if response.status_code != 204:
            error_msg = 'Push failed\n{}'
            raise UploadError(error_msg.format(response.text))
        call(callback, 'push_finish', self.uid)

    def get_finish_push_url(self):
        return get_server_url('/packages/{}/finish'.format(self.uid))

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
