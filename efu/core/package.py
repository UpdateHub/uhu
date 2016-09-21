# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
from collections import OrderedDict

from ..http.request import Request
from ..metadata import ObjectMetadata, PackageMetadata
from ..utils import get_server_url, yes_or_no

from . import Object


DEVICE_OPTIONS = ['truncate', 'seek', 'filesystem']


class Package:

    def __init__(self, version=None, objects=None, product=None):
        self.version = version
        self.objects = objects if objects is not None else {}
        self.product = product
        self.metadata = None

    @classmethod
    def from_file(cls, fn):
        with open(fn) as fp:
            pkg_file = json.load(fp, object_pairs_hook=OrderedDict)
        package = Package(
            version=pkg_file.get('version'), product=pkg_file.get('product'))
        objects = pkg_file.get('objects', {})
        for obj_id, obj in objects.items():
            package.add_object(obj['filename'], obj, obj_id=int(obj_id))
        package.load_metadata()
        return package

    @classmethod
    def from_metadata(cls, metadata):
        package = Package(product=metadata['product'])
        for obj in metadata['objects']:
            options = {option: value for option, value in obj.items()
                       if option not in ObjectMetadata.VOLATILE_OPTIONS}
            metadata = ObjectMetadata(
                obj['filename'], obj['sha256sum'], obj['size'], options)
            package.add_object(
                obj['filename'], options=options, load=False,
                metadata=metadata)
        return package

    def load_metadata(self):
        self.metadata = PackageMetadata(
            self.product, self.version, self.objects.values())

    def serialize(self):
        return {
            'version': self.version,
            'objects': [obj.serialize() for obj in self.objects.values()],
            'metadata': self.metadata.serialize()
        }

    def dump(self, fn, full=False):
        objects = {obj_id: obj.metadata.serialize(full=False)
                   for obj_id, obj in self.objects.items()}
        pkg = {
            'product': self.product,
            'objects': objects,
            'version': self.version if full else None
        }
        with open(fn, 'w') as fp:
            json.dump(pkg, fp)

    def _next_object_id(self):
        ids = self.objects.keys()
        if ids:
            return max(ids) + 1
        return 1

    def add_object(self, fn, options, obj_id=None, load=True, metadata=None):
        obj = Object(fn, options, load=load)
        if metadata is not None:
            obj.metadata = metadata
        if obj_id is None:
            obj_id = self._next_object_id()
        self.objects[obj_id] = obj

    def edit_object(self, obj_id, option, value):
        obj = self.objects[obj_id]
        obj.options[option] = value

    def remove_object(self, obj_id):
        try:
            del self.objects[obj_id]
        except KeyError:
            pass  # already deleted

    @classmethod
    def get_status(cls, product, package_id):
        path = '/products/{product}/packages/{package}/status'
        url = get_server_url(path.format(product=product, package=package_id))
        response = Request(url, 'GET', json=True).send()
        if response.status_code == 200:
            return response.json().get('status')
        raise ValueError('Status not found')

    def __str__(self):
        s = []
        s.append('Product: {}'.format(self.product))
        s.append('Version: {}'.format(self.version))
        if self.objects:
            s.append('Objects:')
        else:
            s.append('Objects: None')
        for obj_id in sorted(self.objects):
            obj = self.objects[obj_id]
            s.append('')
            s.append('  {}# {} [mode: {}]'.format(
                obj_id, obj.metadata.filename, obj.metadata.mode))
            s.append('')
            # compressed option
            compressed = obj.options.get('compressed')
            if compressed is not None:
                line = '      Compressed file:   {}'.format(
                    yes_or_no(compressed))
                if compressed:
                    line += ' [uncompressed size: {}B]'.format(
                        obj.options.get('required-uncompressed-size'))
                s.append(line)
            # device option
            device = obj.options.get('target-device')
            if device is not None:
                line = '      Target device:     {}'.format(device)
                device_options = {option: obj.options.get(option)
                                  for option in DEVICE_OPTIONS}
                if any(device_options.values()):
                    truncate = device_options['truncate']
                    if truncate is not None:
                        device_options['truncate'] = yes_or_no(truncate)
                    device_options = ['{}: {}'.format(k, device_options[k])
                                      for k in sorted(device_options)
                                      if device_options[k] is not None]
                    line += ' [{}]'.format(', '.join(device_options))
                s.append(line)
            # format option
            format_ = obj.options.get('format?')
            if format_ is not None:
                line = '      Format device:     {}'.format(
                    yes_or_no(format_))
                format_options = obj.options.get('format-options')
                if format_options:
                    line += '[options: "{}"]'.format(format_options)
                s.append(line)
            # mount options
            mount = obj.options.get('mount-options')
            if mount is not None:
                s.append('      Mount options:     "{}"'.format(mount))
            # target path option
            path = obj.options.get('target-path')
            if path is not None:
                s.append('      Target path:       {}'.format(path))
            # chunk size option
            chunk = obj.options.get('chunk-size')
            if chunk is not None:
                s.append('      Chunk size:        {}'.format(chunk))
            # skip option
            skip = obj.options.get('skip')
            if skip is not None:
                s.append('      Skip from source:  {}'.format(skip))
            # count option
            count = obj.options.get('count')
            if count is not None:
                s.append('      Count:             {}'.format(count))
        return '\n'.join(s)
