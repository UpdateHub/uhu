# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import math
import os

from ..http import Request
from ..utils import (
    call, get_chunk_size, get_server_url, get_uncompressed_size,
    get_compressor_format, yes_or_no)

from .options import OptionsParser
from .storages import STORAGES


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

    VOLATILE_OPTIONS = ('size', 'sha256sum', 'required-uncompressed-size')
    DEVICE_OPTIONS = ['truncate', 'seek', 'filesystem']

    def __init__(self, uid, fn, mode, options, compressed=None):
        self.uid = uid
        self.filename = fn
        self.mode = mode
        self.options = OptionsParser(self.mode, options).clean()

        self.size = None
        self.sha256sum = None
        self.md5 = None

        self.compressor = None
        self._compressed = compressed

        self.chunk_size = get_chunk_size()

    @property
    def compressed(self):
        # For now, copy objects cannot be decompressed on agent
        if self.mode == 'copy':
            return False
        if self._compressed is None:
            self.compressor = get_compressor_format(self.filename)
            self._compressed = bool(self.compressor)
        return self._compressed

    @property
    def uncompressed_size(self):
        if self.compressed:
            return get_uncompressed_size(self.filename, self.compressor)

    def metadata(self):
        ''' Serialize object as metadata '''
        metadata = {
            'filename': self.filename,
            'mode': self.mode,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'compressed': self.compressed,
        }
        if self.compressed:
            metadata['required-uncompressed-size'] = self.uncompressed_size
        metadata.update(self.options)
        return metadata

    def template(self):
        ''' Serialize object for dumping to a file '''
        return {
            'filename': self.filename,
            'mode': self.mode,
            'compressed': self.compressed,
            'options': self.options,
        }

    def load(self, callback=None):
        self.size = os.path.getsize(self.filename)
        call(callback, 'pre_object_load', self)
        sha256sum = hashlib.sha256()
        md5 = hashlib.md5()
        for chunk in self:
            sha256sum.update(chunk)
            md5.update(chunk)
            call(callback, 'object_load', self)
        self.sha256sum = sha256sum.hexdigest()
        self.md5 = md5.hexdigest()
        call(callback, 'post_object_load', self)

    def upload(self, product_uid, package_uid, callback=None):
        from ..transactions.exceptions import UploadError
        call(callback, 'pre_object_upload', self)
        url = get_server_url('/products/{}/packages/{}/objects/{}'.format(
            product_uid, package_uid, self.sha256sum))
        body = json.dumps({'etag': self.md5})
        response = Request(url, 'POST', body, json=True).send()
        if response.status_code == 200:
            call(callback, 'post_object_upload',
                 self, ObjectUploadResult.EXISTS)
            return ObjectUploadResult.EXISTS
        elif response.status_code == 201:
            body = response.json()
            storage = STORAGES[body['storage']](self, callback=callback)
            upload_url = body['url']
            storage.upload(upload_url)
            if storage.success:
                call(callback, 'post_object_upload',
                     self, ObjectUploadResult.SUCCESS)
                return ObjectUploadResult.SUCCESS
            call(callback, 'post_object_upload', self, ObjectUploadResult.FAIL)
            return ObjectUploadResult.FAIL
        else:
            call(callback, 'post_object_upload', self, ObjectUploadResult.FAIL)
            errors = response.json().get('errors', [])
            error_msg = 'It was not possible to get url:\n{}'
            raise UploadError(error_msg.format('\n'.join(errors)))

    def __len__(self):
        return math.ceil(self.size/self.chunk_size)

    def __iter__(self):
        with open(self.filename, 'br') as fp:
            for chunk in iter(lambda: fp.read(self.chunk_size), b''):
                yield chunk

    def __str__(self):
        s = []
        s.append('  {}# {} [mode: {}]'.format(
            self.uid, self.filename, self.mode))
        s.append('')
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
