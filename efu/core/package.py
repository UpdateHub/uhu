# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..metadata import PackageMetadata
from ..utils import yes_or_no

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
            package = json.load(fp)

        file_objects = package.get('objects')
        product = package.get('product')
        version = package.get('version')
        objects = {}
        if file_objects is not None:
            for fn, options in file_objects.items():
                obj = Object(fn, options)
                objects[obj.filename] = obj
        package = Package(version=version, objects=objects, product=product)
        package.load_metadata()
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
        objects = {obj.filename: obj.metadata.serialize(full=False)
                   for obj in self.objects.values()}
        pkg = {
            'product': self.product,
            'objects': objects,
            'version': self.version if full else None
        }
        with open(fn, 'w') as fp:
            json.dump(pkg, fp)

    def remove_object(self, fn):
        try:
            del self.objects[fn]
        except KeyError:
            pass  # alredy deleted

    def __str__(self):
        s = []
        s.append('Product: {}'.format(self.product))
        s.append('')
        s.append('Objects:')
        for fn in sorted(self.objects):
            obj = self.objects[fn]
            s.append('')
            s.append('  {} [install mode: {}]'.format(
                fn, obj.metadata.install_mode))
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
        s.append('')
        return '\n'.join(s)
