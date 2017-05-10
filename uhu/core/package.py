# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import hashlib
import json
from collections import OrderedDict

import requests
from pkgschema import validate_metadata

from ..exceptions import DownloadError, UploadError
from ..http.request import Request
from ..utils import call, get_server_url

from .hardware import HardwareManager
from .object import Object, ObjectUploadResult
from .manager import InstallationSetManager, InstallationSetMode


MODES = ['single', 'active-inactive']


class Package:
    """A package represents a group of objects."""

    def __init__(self, mode, uid=None, version=None, product=None):
        self.mode = mode
        self.uid = uid
        self.version = version
        self.product = product
        self.objects = InstallationSetManager(self.mode)
        self.hardwares = HardwareManager()

    @classmethod
    def from_file(cls, fn):
        """Creates a package from a dumped package."""
        with open(fn) as fp:
            dump = json.load(fp, object_pairs_hook=OrderedDict)
        objects = dump.get('objects', [])
        package = Package(
            mode=InstallationSetMode.from_objects(objects),
            version=dump.get('version'),
            product=dump.get('product'))
        package.hardwares = HardwareManager(dump.get('supported-hardware'))
        blacklist = ('mode',)
        for set_index, installation_set in enumerate(objects):
            for obj in installation_set:
                options = {option: value
                           for option, value in obj.items()
                           if option not in blacklist}
                set_ = package.objects.get_installation_set(set_index)
                set_.create(mode=obj['mode'], options=options)
        return package

    @classmethod
    def from_metadata(cls, metadata):
        """Creates a package from a metadata object."""
        objects = metadata['objects']
        package = Package(
            mode=InstallationSetMode.from_objects(objects),
            version=metadata['version'],
            product=metadata['product'])
        # Supported hardwares
        hardwares = metadata.get('supported-hardware', [])
        for hardware in hardwares:
            name = hardware['hardware']
            revision = hardware.get('hardware-rev')
            hardware = package.hardwares.get(name)
            if hardware is None:
                package.hardwares.add(name)
            if revision is not None:
                package.hardwares.add_revision(name, revision)
        # Objects
        for set_index, installation_set in enumerate(objects):
            for obj in installation_set:
                blacklist = ('mode', 'install-if-different')
                options = {option: value
                           for option, value in obj.items()
                           if option not in blacklist}
                install_if_different = obj.get('install-if-different')
                if install_if_different is not None:
                    options.update(Object.to_install_condition(obj))
                set_ = package.objects.get_installation_set(set_index)
                set_.create(mode=obj['mode'], options=options)
        return package

    def metadata(self):
        """Serialize package as metadata."""
        metadata = {
            'product': self.product,
            'version': self.version,
            'objects': self.objects.metadata(),
        }
        if self.hardwares.count():
            metadata['supported-hardware'] = self.hardwares.metadata()
        return metadata

    def template(self):
        """Serialize package to dump to a file."""
        return {
            'version': self.version,
            'product': self.product,
            'supported-hardware': self.hardwares.template(),
            'objects': self.objects.template(),
        }

    def export(self, dest):
        """Writes package template in dest file (without version)."""
        template = self.template()
        template['version'] = None
        self._persist(template, dest)

    def dump(self, dest):
        """Writes package template in dest file (with version)."""
        self._persist(self.template(), dest)

    def _persist(self, dict_, fn):
        """Saves an dict_ as JSON into fn."""
        with open(fn, 'w') as fp:
            json.dump(dict_, fp, indent=4, sort_keys=True)

    def upload_metadata(self):
        metadata = self.metadata()
        validate_metadata(metadata)
        payload = json.dumps(metadata)
        url = self.get_metadata_upload_url()
        response = Request(
            url, method='POST', payload=payload, json=True).send()
        response_body = response.json()
        if response.status_code != 201:
            errors = '\n'.join(response_body.get('errors', []))
            error_msg = 'It was not possible to start pushing:\n{}'
            raise UploadError(error_msg.format(errors))
        self.uid = response_body['package-uid']

    def upload_objects(self, callback=None):
        results = []
        objects = self.objects.get_installation_set(index=0)
        call(callback, 'start_package_upload', objects)
        for obj in objects:
            results.append(obj.upload(self.product, self.uid, callback))
        call(callback, 'finish_package_upload')
        for result in results:
            if not ObjectUploadResult.is_ok(result):
                err = 'Some objects has not been fully uploaded'
                raise UploadError(err)

    def finish_push(self, callback=None):
        response = Request(self.get_finish_push_url(), 'POST').send()
        if response.status_code != 202:
            error_msg = 'Push failed\n{}'
            raise UploadError(error_msg.format(response.text))
        call(callback, 'push_finish', self.uid)

    def get_finish_push_url(self):
        return get_server_url('/products/{}/packages/{}/finish'.format(
            self.product, self.uid))

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
            url = self.get_object_download_url(uid, obj)
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

    def get_object_download_url(self, uid, obj):
        path = '/products/{}/packages/{}/objects/{}'.format(
            self.product, uid, obj['sha256sum'])
        return get_server_url(path)

    def get_metadata_upload_url(self):
        return get_server_url('/packages')

    def get_status(self):
        path = '/packages/{package}'
        url = get_server_url(path.format(package=self.uid))
        response = Request(url, 'GET', json=True).send()
        if response.status_code != 200:
            raise ValueError('Status not found')
        return response.json().get('status')

    def __str__(self):
        return '\n'.join([
            'Product: {}'.format(self.product),
            'Version: {}'.format(self.version),
            str(self.hardwares),
            str(self.objects),
        ])
