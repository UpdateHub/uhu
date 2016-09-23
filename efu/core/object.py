# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os

from ..http import Request
from ..utils import get_chunk_size, yes_or_no

from .options import OptionsParser


class ObjectUploadResult:
    SUCCESS = 1
    EXISTS = 2
    FAIL = 3

    OK_RESULTS = (SUCCESS, EXISTS)

    @classmethod
    def is_ok(cls, result):
        return result in cls.OK_RESULTS


class Object:
    '''
    Objects represents a file or a image with instructions (metadata)
    to agent operate it.
    '''

    VOLATILE_OPTIONS = ('size', 'sha256sum')
    DEVICE_OPTIONS = ['truncate', 'seek', 'filesystem']

    def __init__(self, uid, fn, mode, options):
        self.uid = uid
        self.filename = fn
        self.mode = mode
        self.options = OptionsParser(self.mode, options).clean()

        self.size = None
        self.sha256sum = None
        self.chunks = []
        self.chunk_size = get_chunk_size()

    def serialize(self):
        ''' Serialize object to send to server '''
        return {
            'id': self.uid,
            'chunks': self.chunks,
            'metadata': self.metadata()
        }

    def metadata(self):
        ''' Serialize object as metadata '''
        metadata = {
            'filename': self.filename,
            'mode': self.mode,
            'sha256sum': self.sha256sum,
            'size': self.size,
        }
        metadata.update(self.options)
        return metadata

    def template(self):
        ''' Serialize object for dumping to a file '''
        return {
            'filename': self.filename,
            'mode': self.mode,
            'options': self.options,
        }

    def load(self, callback=None):
        self.size = os.path.getsize(self.filename)
        sha256sum = hashlib.sha256()

        if callback is not None:
            callback.pre_object_load(self)
        for position, chunk in enumerate(self):
            sha256sum.update(chunk)
            self.chunks.append({
                'position': position,
                'sha256sum': hashlib.sha256(chunk).hexdigest()
            })
            if callback is not None:
                callback.object_load(self)
        self.sha256sum = sha256sum.hexdigest()
        if callback is not None:
            callback.post_object_load(self)

    def upload(self, conf, callback=None):
        if callback is not None:
            callback.pre_object_upload(self)
        result = ObjectUploadResult.SUCCESS
        if conf['exists']:
            result = ObjectUploadResult.EXISTS
        else:
            for position, chunk in enumerate(self):
                chunk_conf = conf['chunks'][str(position)]
                if chunk_conf['exists']:
                    continue
                response = Request(chunk_conf['url'], 'POST', chunk).send()
                if response.status_code != 201:
                    result = ObjectUploadResult.FAIL
                if callback is not None:
                    callback.object_upload(self)
        if callback is not None:
            callback.post_object_upload(self)
        return result

    def __len__(self):
        return len(self.chunks)

    def __iter__(self):
        with open(self.filename, 'br') as fp:
            for chunk in iter(lambda: fp.read(self.chunk_size), b''):
                yield chunk

    def __str__(self):
        s = []
        s.append('  {}# {} [mode: {}]'.format(
            self.uid, self.filename, self.mode))
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
                              for option in self.DEVICE_OPTIONS}
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
            line = '      Format device:     {} '.format(yes_or_no(format_))
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
