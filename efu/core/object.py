# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import itertools
import os

from ..metadata import ObjectMetadata
from ..utils import get_chunk_size, yes_or_no


DEVICE_OPTIONS = ['truncate', 'seek', 'filesystem']


class Chunk:

    def __new__(cls, *args):
        ''' Returns None if data (args[0]) is empty '''
        return super().__new__(cls) if args[0] else None

    def __init__(self, data, number):
        self.data = data
        self.number = number
        self.sha256sum = hashlib.sha256(self.data).hexdigest()

    def serialize(self):
        return {
            'sha256sum': self.sha256sum,
            'number': self.number,
        }


class Object:

    def __init__(self, fn, options=None):
        self.filename = fn
        self.options = options
        self.size = None
        self.chunks = []
        self.sha256sum = None
        self.metadata = None
        self.loaded = False

        self._fd = None
        self._chunk_number = itertools.count()

    def load(self):
        if self.loaded:
            return
        self._fd = open(self.filename, 'br')
        self.size = os.path.getsize(self.filename)

        sha256sum = hashlib.sha256()
        for chunk in self:
            self.chunks.append(chunk.serialize())
            sha256sum.update(chunk.data)
        self.sha256sum = sha256sum.hexdigest()
        self.metadata = ObjectMetadata(
            self.filename, self.sha256sum, self.size, self.options)
        self.loaded = True

    def serialize(self):
        self.load()
        return {
            'sha256sum': self.sha256sum,
            'parts': self.chunks,
            'metadata': self.metadata.serialize()
        }

    def _read(self):
        data = self._fd.read(get_chunk_size())
        return Chunk(data, next(self._chunk_number))

    def __iter__(self):
        return iter(self._read, None)

    def __len__(self):
        return len(self.chunks)

    def __str__(self):
        s = []
        s.append('{} [mode: {}]'.format(self.filename, self.metadata.mode))
        s.append('')
        # compressed option
        compressed = self.options.get('compressed')
        if compressed is not None:
            line = '      Compressed file:   {}'.format(yes_or_no(compressed))
            if compressed:
                line += ' [uncompressed size: {}B]'.format(
                    self.options.get('required-uncompressed-size'))
            s.append(line)
        # device option
        device = self.options.get('target-device')
        if device is not None:
            line = '      Target device:     {}'.format(device)
            device_options = {option: self.options.get(option)
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
        format_ = self.options.get('format?')
        if format_ is not None:
            line = '      Format device:     {}'.format(yes_or_no(format_))
            format_options = self.options.get('format-options')
            if format_options:
                line += '[options: "{}"]'.format(format_options)
            s.append(line)
        # mount options
        mount = self.options.get('mount-options')
        if mount is not None:
            s.append('      Mount options:     "{}"'.format(mount))
        # target path option
        path = self.options.get('target-path')
        if path is not None:
            s.append('      Target path:       {}'.format(path))
        # chunk size option
        chunk = self.options.get('chunk-size')
        if chunk is not None:
            s.append('      Chunk size:        {}'.format(chunk))
        # skip option
        skip = self.options.get('skip')
        if skip is not None:
            s.append('      Skip from source:  {}'.format(skip))
        # count option
        count = self.options.get('count')
        if count is not None:
            s.append('      Count:             {}'.format(count))
        return '\n'.join(s)
