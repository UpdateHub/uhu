# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
from collections import OrderedDict

import requests

from ..exceptions import DownloadError, UploadError
from ..http.request import Request
from ..utils import call, get_server_url, validate_schema

from .object import Object, ObjectUploadResult
from .installation_set import InstallationSetManager, InstallationSetMode


MODES = ['single', 'active-inactive']


class Package:
    """A package represents a group of objects."""

    def __init__(self, mode, uid=None, version=None, product=None):
        self.mode = mode
        self.uid = uid
        self.version = version
        self.product = product
        self.objects = InstallationSetManager(self.mode)
        self.supported_hardware = {}

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
        package.supported_hardware = dump.get('supported-hardware', {})
        for set_index, installation_set in enumerate(objects):
            for obj in installation_set:
                set_ = package.objects.get_installation_set(set_index)
                set_.create(
                    fn=obj['filename'],
                    mode=obj['mode'],
                    options=obj['options'])
        return package

    @classmethod
    def from_metadata(cls, metadata):
        """Creates a package from a metadata object."""
        objects = metadata['objects']
        package = Package(
            mode=InstallationSetMode.from_objects(objects),
            version=metadata['version'],
            product=metadata['product'])
        for set_index, installation_set in enumerate(objects):
            for obj in installation_set:
                blacklist = (
                    'filename', 'mode', 'compressed', 'install-if-different')
                options = {option: value
                           for option, value in obj.items()
                           if option not in blacklist}
                install_if_different = obj.get('install-if-different')
                if install_if_different is not None:
                    options.update(Object.to_install_condition(obj))
                set_ = package.objects.get_installation_set(set_index)
                set_.create(
                    fn=obj['filename'],
                    mode=obj['mode'],
                    options=options,
                    sha256sum=obj['sha256sum'])
        return package

    def add_supported_hardware(self, name, revisions=None):
        revisions = revisions if revisions is not None else []
        self.supported_hardware[name] = {
            'name': name,
            'revisions': sorted([rev for rev in revisions])
        }

    def remove_supported_hardware(self, hardware):
        supported_hardware = self.supported_hardware.pop(hardware, None)
        if supported_hardware is None:
            err = 'Hardware {} does not exist or is already removed.'
            raise ValueError(err.format(hardware))

    def add_supported_hardware_revision(self, hardware, revision):
        supported_hardware = self.supported_hardware.get(hardware)
        if supported_hardware is None:
            err = 'Hardware {} does not exist'.format(hardware)
            raise ValueError(err)
        if revision not in supported_hardware['revisions']:
            supported_hardware['revisions'].append(revision)
        supported_hardware['revisions'].sort()

    def remove_supported_hardware_revision(self, hardware, revision):
        supported_hardware = self.supported_hardware.get(hardware)
        if supported_hardware is None:
            err = 'Hardware {} does not exist'.format(hardware)
            raise ValueError(err)
        try:
            supported_hardware['revisions'].remove(revision)
        except ValueError:
            err = 'Revision {} for {} does not exist or is already removed'
            raise ValueError(err.format(revision, hardware))

    def metadata(self):
        """Serialize package as metadata."""
        metadata = {
            'product': self.product,
            'version': self.version,
            'objects': self.objects.metadata(),
        }
        if self.supported_hardware:
            metadata['supported-hardware'] = self.supported_hardware
        return metadata

    def template(self):
        """Serialize package to dump to a file."""
        return {
            'version': self.version,
            'product': self.product,
            'supported-hardware': self.supported_hardware,
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
        validate_schema('metadata.json', metadata)
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
        call(callback, 'push_finish', self, response)
        if response.status_code != 202:
            error_msg = 'Push failed\n{}'
            raise UploadError(error_msg.format(response.text))

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
            if not obj.exists():
                objects.append(obj)
                continue  # File does not exist, must be downloaded
            sha256sum = hashlib.sha256()
            for chunk in obj:
                sha256sum.update(chunk)
            if sha256sum.hexdigest() != obj.sha256sum:
                # Local object diverges from server object, must abort
                raise DownloadError(
                    '{} will be overwritten'.format(obj.filename))
            # If we got here, means that object exists locally and
            # is equal to remote object. Therefore, it must be not
            # downloaded.
        return objects

    def get_object_download_url(self, uid, obj):
        path = '/products/{}/packages/{}/objects/{}'.format(
            self.product, uid, obj.sha256sum)
        return get_server_url(path)

    def get_metadata_upload_url(self):
        return get_server_url(
            '/products/{}/packages'.format(self.product))

    def get_status(self):
        path = '/products/{product}/packages/{package}/status'
        url = get_server_url(
            path.format(product=self.product, package=self.uid))
        response = Request(url, 'GET', json=True).send()
        if response.status_code != 200:
            raise ValueError('Status not found')
        return response.json().get('status')

    def __str__(self):
        s = []
        # Product
        s.append('Product: {}'.format(self.product))
        # Version
        s.append('Version: {}'.format(self.version))
        # Supported hardware
        if self.supported_hardware:
            s.append('Supported hardware:')
            s.append('')
            for i, name in enumerate(sorted(self.supported_hardware), 1):
                revisions = ', '.join(
                    self.supported_hardware[name]['revisions'])
                revisions = revisions if revisions else 'all'
                s.append('  {}# {} [revisions: {}]'.format(i, name, revisions))
                s.append('')
        else:
            s.append('Supported hardware: all')
        # Objects
        if len(self.objects.all()):
            s.append(str(self.objects))
        else:
            s.append('Objects: None')
        return '\n'.join(s)
