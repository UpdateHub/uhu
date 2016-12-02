# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
from collections import OrderedDict

from ..exceptions import UploadError
from ..http.request import Request
from ..utils import call, get_server_url, validate_schema

from .object import Object, ObjectUploadResult
from .installation_set import InstallationSetManager, InstallationSetMode


MODES = ['single', 'active-inactive']
ACTIVE_INACTIVE_MODES = ['u-boot']


class Package:
    """A package represents a group of objects."""

    def __init__(self, mode, uid=None, version=None, product=None):
        self.mode = mode
        self.uid = uid
        self.version = version
        self.product = product
        self.objects = InstallationSetManager(self.mode)
        self.supported_hardware = {}
        self._active_inactive_backend = None

    @classmethod
    def from_file(cls, fn):
        """Creates a package from a dumped package."""
        with open(fn) as fp:
            dump = json.load(fp, object_pairs_hook=OrderedDict)
        objects = dump.get('objects')
        package = Package(
            mode=InstallationSetMode.from_objects(objects),
            version=dump.get('version'),
            product=dump.get('product'))
        package.supported_hardware = dump.get('supported-hardware', {})
        package.active_inactive_backend = dump.get('active-inactive-backend')
        for set_index, installation_set in enumerate(objects):
            for obj in installation_set:
                set_ = package.objects.get_installation_set(set_index)
                set_.add(Object(
                    fn=obj['filename'], mode=obj['mode'],
                    options=obj['options'], compressed=obj.get('compressed')))
        return package

    @classmethod
    def from_metadata(cls, metadata):
        """Creates a package from a metadata object."""
        objects = metadata['objects']
        package = Package(
            mode=InstallationSetMode.from_objects(objects),
            version=metadata['version'],
            product=metadata['product'])
        package.active_inactive_backend = metadata.get(
            'active-inactive-backend')
        for set_index, installation_set in enumerate(objects):
            for obj in installation_set:
                settings = (
                    'filename', 'mode', 'compressed', 'install-if-different')
                options = {option: value
                           for option, value in obj.items()
                           if option not in settings}
                install_if_different = obj.get('install-if-different')
                if install_if_different is not None:
                    options.update(Object.to_install_condition(obj))
                set_ = package.objects.get_installation_set(set_index)
                set_.add(Object(
                    fn=obj['filename'], mode=obj['mode'],
                    sha256sum=obj['sha256sum'], options=options))
        return package

    @property
    def active_inactive_backend(self):
        return self._active_inactive_backend

    @active_inactive_backend.setter
    def active_inactive_backend(self, backend):
        if backend not in ACTIVE_INACTIVE_MODES and backend is not None:
            err = '"{}" is not a valid active-inactive backend mode'
            raise ValueError(err.format(backend))
        self._active_inactive_backend = backend

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

    def load(self, callback=None):
        call(callback, 'pre_package_load')
        for obj in self.objects.all():
            obj.load(callback)
            call(callback, 'package_load')
        call(callback, 'post_package_load')

    def metadata(self):
        ''' Serialize package as metadata '''
        metadata = {
            'product': self.product,
            'version': self.version,
            'objects': self.objects.metadata(),
        }
        if self.supported_hardware:
            metadata['supported-hardware'] = self.supported_hardware
        if self.active_inactive_backend:
            metadata['active-inactive-backend'] = self.active_inactive_backend
        return metadata

    def template(self):
        ''' Serialize package to dump to a file '''
        return {
            'version': self.version,
            'product': self.product,
            'supported-hardware': self.supported_hardware,
            'objects': self.objects.template(),
            'active-inactive-backend': self.active_inactive_backend,
        }

    def export(self, dest):
        ''' Writes package template in dest file (without version) '''
        template = self.template()
        template['version'] = None
        self._persist(template, dest)

    def dump(self, dest):
        ''' Writes package template in dest file (with version) '''
        self._persist(self.template(), dest)

    def _persist(self, dict_, fn):
        ''' Saves an dict_ as JSON into fn '''
        with open(fn, 'w') as fp:
            json.dump(dict_, fp, indent=4, sort_keys=True)

    def upload_metadata(self, callback=None):
        metadata = self.metadata()
        validate_schema('metadata.json', metadata)
        payload = json.dumps(metadata)
        url = self.get_metadata_upload_url()
        response = Request(
            url, method='POST', payload=payload, json=True).send()
        call(callback, 'push_start', response)
        response_body = response.json()
        if response.status_code != 201:
            errors = '\n'.join(response_body.get('errors', []))
            error_msg = 'It was not possible to start pushing:\n{}'
            raise UploadError(error_msg.format(errors))
        self.uid = response_body['package-uid']

    def upload_objects(self, callback=None):
        results = []
        for obj in self.objects.all():
            results.append(obj.upload(self.product, self.uid, callback))
        for result in results:
            if not ObjectUploadResult.is_ok(result):
                err = 'Some objects has not been fully uploaded'
                raise UploadError(err)

    def finish_push(self, callback=None):
        response = Request(self.get_finish_push_url(), 'POST').send()
        call(callback, 'push_finish', self, response)
        if response.status_code != 202:
            errors = '\n'.join(response.json()['errors'])
            error_msg = 'It was not possible to finish pushing:\n{}'
            raise UploadError(error_msg.format(errors))

    def get_finish_push_url(self):
        return get_server_url('/products/{}/packages/{}/finish'.format(
            self.product, self.uid))

    def push(self, callback=None):
        self.upload_metadata(callback)
        self.upload_objects(callback)
        self.finish_push(callback)

    def download_metadata(self):
        path = '/products/{}/packages/{}'.format(self.product, self.uid)
        response = Request(get_server_url(path), 'GET').send()
        if not response.ok:
            raise ValueError('Package not found')
        return response.json()

    def get_download_list(self):
        '''
        Returns a list with all objects that must be downloaded.

        If local object exists and it is equal to remote object, we
        do not downloaded it.  Verifies if local files will not be
        overwritten by incoming files.

        If local objects exists and it is different from remote
        object, we raise an exception to avoid object overwritting.
        '''
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
                raise FileExistsError(
                    '{} will be overwritten', obj.filename)
            # If we got here, means that object exists locally and
            # is equal to remote object. Therefore, it must be not
            # downloaded.
        return objects

    def get_metadata_upload_url(self):
        return get_server_url(
            '/products/{}/packages'.format(self.product))

    def get_object_download_url(self, obj):
        path = '/products/{}/packages/{}/objects/{}'.format(
            self.product, self.uid, obj.sha256sum)
        return get_server_url(path)

    def pull(self, full=True):
        metadata = self.download_metadata()
        package = Package.from_metadata(metadata)
        if full:
            objects = package.get_download_list()
            for obj in objects:
                obj.download(self.get_object_download_url(obj))
        return package

    def get_status(self):
        path = '/products/{product}/packages/{package}/status'
        url = get_server_url(
            path.format(product=self.product, package=self.uid))
        response = Request(url, 'GET', json=True).send()
        if response.status_code != 200:
            raise ValueError('Status not found')
        return response.json().get('status')

    def __len__(self):
        return len(self.objects)

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
        # ActiveInactive
        s.append('Active-Inactive Backend: {}'.format(
            self.active_inactive_backend))
        # Objects
        if len(self.objects.all()):
            s.append(str(self.objects))
        else:
            s.append('Objects: None')
        return '\n'.join(s)
