# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
from collections import OrderedDict

from ..http.request import Request
from ..transactions import Pull, Push
from ..utils import get_server_url

from . import Object


class Package:
    ''' A package represents a group of objects. '''

    def __init__(self, uid=None, version=None, product=None):
        self.uid = uid
        self.version = version
        self.product = product
        self.objects = {}

    @classmethod
    def from_file(cls, fn):
        ''' Creates a package from a dumped package '''
        with open(fn) as fp:
            dump = json.load(fp, object_pairs_hook=OrderedDict)
        package = Package(
            version=dump.get('version'), product=dump.get('product'))
        objects = dump.get('objects', {})
        for obj_uid, conf in objects.items():
            package.add_object(
                uid=int(obj_uid), fn=conf['filename'],
                mode=conf['mode'], options=conf['options'])
        return package

    @classmethod
    def from_metadata(cls, metadata):
        ''' Creates a package from a metadata object '''
        package = Package(
            product=metadata['product'], version=metadata['version'])
        for obj_metadata in metadata['objects']:
            options = {option: value for option, value in obj_metadata.items()
                       if option not in ('filename', 'mode')}
            obj = package.add_object(
                obj_metadata['filename'], obj_metadata['mode'], options)
            obj.size = obj_metadata['size']
            obj.sha256sum = obj_metadata['sha256sum']
        return package

    def add_object(self, fn, mode, options, uid=None):
        ''' Adds a new object within package. Returns an Object instance '''
        if uid is None:
            uid = self._next_object_id()
        obj = Object(uid, fn, mode, options)
        self.objects[uid] = obj
        return obj

    def edit_object(self, uid, option, value):
        ''' Given an object id, sets obj.option to value '''
        obj = self.objects[uid]
        obj.options[option] = value

    def remove_object(self, uid):
        ''' Removes an object from package '''
        del self.objects[uid]

    def load(self, callback=None):
        if callback is not None:
            callback.pre_package_load(self)
        for obj in self:
            obj.load(callback)
            if callback is not None:
                callback.package_load(self)
        if callback is not None:
            callback.post_package_load(self)

    def serialize(self):
        ''' Serialize package to send to server '''
        return {
            'version': self.version,
            'objects': [obj.serialize() for obj in self],
            'metadata': self.metadata()
        }

    def metadata(self):
        ''' Serialize package as metadata '''
        return {
            'product': self.product,
            'version': self.version,
            'objects': [obj.metadata() for obj in self],
        }

    def template(self):
        ''' Serialize package to dump to a file '''
        return {
            'version': self.version,
            'product': self.product,
            'objects': {obj.uid: obj.template() for obj in self}
        }

    def dump(self, dest):
        ''' Writes package template in dest file '''
        with open(dest, 'w') as fp:
            json.dump(self.template(), fp)

    def push(self, callback=None):
        push = Push(self, callback)
        push.start_push()
        push.upload_objects()
        push.finish_push()

    def pull(self, full=True):
        pull = Pull(self)
        pull.get_metadata()
        package = Package.from_metadata(pull.metadata)
        if full:
            pull.check_local_files(package)
            for obj in package:
                pull.download_object(obj)
        return package

    def get_status(self):
        path = '/products/{product}/packages/{package}/status'
        url = get_server_url(
            path.format(product=self.product, package=self.uid))
        response = Request(url, 'GET', json=True).send()
        if response.status_code != 200:
            raise ValueError('Status not found')
        return response.json().get('status')

    def _next_object_id(self):
        ''' Genretares objects ids '''
        ids = self.objects.keys()
        if ids:
            return max(ids) + 1
        return 1

    def __len__(self):
        return len(self.objects)

    def __iter__(self):
        return iter(self.objects.values())

    def __str__(self):
        s = []
        s.append('Product: {}'.format(self.product))
        s.append('Version: {}'.format(self.version))
        if self.objects:
            s.append('Objects:')
        else:
            s.append('Objects: None')
        for uid in sorted(self.objects):
            s.append('')
            s.append(str(self.objects[uid]))
        return '\n'.join(s)
