# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib

from .. import http
from ..exceptions import DownloadError
from ..utils import get_server_url

from .hardware import SupportedHardwareManager
from .objects import ObjectsManager
from .updatehub import upload_metadata, finish_package, upload_objects


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
        """Uploads package metadata to server."""
        metadata = self.to_metadata()
        self.uid = upload_metadata(metadata)

    def upload_objects(self, callback=None):
        """Uploads package objects."""
        objects = self.objects[0]  # this means first installation set
        return upload_objects(self.uid, objects, callback)

    def finish_push(self, callback=None):
        """Tells server that package upload is finished."""
        return finish_package(self.uid, callback)

    def push(self, callback=None):
        self.upload_metadata()
        self.upload_objects(callback)
        self.finish_push(callback)

    @classmethod
    def download_metadata(cls, uid):
        url = get_server_url('/packages/{}'.format(uid))
        response = http.get(url)
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

    def __str__(self):
        return '\n'.join([
            'Product: {}'.format(self.product),
            'Version: {}'.format(self.version),
            str(self.supported_hardware),
            str(self.objects),
        ])
