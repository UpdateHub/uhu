# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import math
import os
from collections import OrderedDict

from humanize.filesize import naturalsize

from ..http import Request
from ..utils import (
    call, get_chunk_size, get_server_url, get_uncompressed_size,
    get_compressor_format, indent, yes_or_no)

from .options import OptionsParser
from .storages import STORAGES


OBJECT_STRING_TEMPLATE = OrderedDict([
    ('target-device', OrderedDict([
        ('display', 'Target device:'),
        ('children', OrderedDict([
            ('seek', OrderedDict([
                ('display', 'seek:'),
            ])),
            ('truncate', OrderedDict([
                ('display', 'truncate:'),
                ('bool', True),
            ])),
            ('filesystem', OrderedDict([
                ('display', 'filesystem:'),
            ])),
        ])),
    ])),
    ('format?', OrderedDict([
        ('display', 'Format device:'),
        ('bool', True),
        ('children', OrderedDict([
            ('format-options', OrderedDict([
                ('display', 'options:'),
                ('wrap', True),
            ])),
        ])),
    ])),
    ('mount-options', OrderedDict([
        ('display', 'Mount options:'),
        ('wrap', True),
    ])),
    ('target-path', OrderedDict([
        ('display', 'Target path:'),
    ])),
    ('chunk-size', OrderedDict([
        ('display', 'Chunk size:'),
        ('bytes', True),
    ])),
    ('skip', OrderedDict([
        ('display', 'Skip from source:'),
    ])),
    ('count', OrderedDict([
        ('display', 'Count:'),
    ])),
])


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

    def __init__(self, fn, mode, options, compressed=None):
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

    def exists(self):
        return os.path.exists(self.filename)

    def download(self, url):
        if self.exists():
            return
        from ..transactions.exceptions import DownloadError
        response = Request(url, 'GET', stream=True).send()
        if not response.ok:
            errors = response.json().get('errors', [])
            error_msg = 'It was not possible to download object:\n{}'
            raise DownloadError(error_msg.format('\n'.join(errors)))
        with open(self.filename, 'wb') as fp:
            for chunk in response.iter_content():
                fp.write(chunk)

    def __len__(self):
        if self.size is not None:
            return math.ceil(self.size/self.chunk_size)
        raise RuntimeError('Object is not loaded.')

    def __iter__(self):
        with open(self.filename, 'br') as fp:
            for chunk in iter(lambda: fp.read(self.chunk_size), b''):
                yield chunk

    def _str_value(self, option, conf):
        value = self.options.get(option)
        if conf.get('bool', False):
            value = yes_or_no(value)
        if conf.get('wrap', False):
            value = '"{}"'.format(value)
        if conf.get('bytes', False):
            value = naturalsize(value, binary=True)
        return value

    def _str_children(self, conf):
        options = conf.get('children')
        s = []
        if options is not None:
            for option, conf in options.items():
                if option in self.options:
                    value = self._str_value(option, conf)
                    s.append('{} {}'.format(conf['display'], value))
        if s:
            return '[{}]'.format(', '.join(s))
        return ''

    def __str__(self):
        s = []
        header = '{} [mode: {}]\n'.format(self.filename, self.mode)
        s.append(header)
        for option, conf in OBJECT_STRING_TEMPLATE.items():
            if option in self.options:
                value = self._str_value(option, conf)
                line = '    {:<18} {} {}'.format(
                    conf['display'], value, self._str_children(conf))
                s.append(line.rstrip())
        return '\n'.join(s)


class ObjectList:
    '''
    Low level package objects manager.
    Represents a list o Object instances
    '''

    def __init__(self):
        self._objects = []

    def add(self, *args, **kwargs):
        ''' Adds an object instance. Returns an Object instance '''
        obj = Object(*args, **kwargs)
        self._objects.append(obj)
        return obj

    def get(self, index):
        ''' Retrives an object by index '''
        try:
            return self._objects[index]
        except IndexError:
            raise ValueError('Object not found')

    def update(self, index, option, value):
        ''' Given an object id, sets obj.option to value '''
        obj = self.get(index)
        obj.options[option] = value
        self._objects[index] = Object(obj.filename, obj.mode, obj.options)

    def remove(self, index):
        ''' Removes an object '''
        try:
            return self._objects.pop(index)
        except IndexError:
            raise ValueError('Object not found')

    def metadata(self):
        return [obj.metadata() for obj in self]

    def template(self):
        return [obj.template() for obj in self]

    def __iter__(self):
        return iter(obj for obj in self._objects)

    def __len__(self):
        return len(self._objects)

    def __str__(self):
        s = []
        s.append('Installation Set:\n')
        for index, obj in enumerate(self):
            s.append('    {}# {}\n'.format(index, indent(str(obj), 4)))
        return '\n'.join(s)


class ObjectManager:
    '''
    High level package objects manager.
    Represents a list of ObjectList instances.
    '''

    def __init__(self):
        self._lists = []

    def add_list(self):
        ''' Creates a new object list '''
        objects = ObjectList()
        self._lists.append(objects)
        return objects

    def get_list(self, index):
        ''' Returns an object list'''
        try:
            return self._lists[index]
        except IndexError:
            raise ValueError('Object List not found')

    def remove_list(self, index):
        ''' Removes an object list '''
        try:
            self._lists.pop(index)
        except IndexError:
            raise ValueError('Object List not found')

    def add(self, index, *args, **kw):
        ''' Adds a new object in a given object list '''
        objects = self.get_list(index)
        return objects.add(*args, **kw)

    def get(self, index, *args, **kw):
        ''' Retrives an object '''
        objects = self.get_list(index)
        return objects.get(*args, **kw)

    def update(self, index, *args, **kw):
        ''' Updates an object option '''
        objects = self.get_list(index)
        objects.update(*args, **kw)

    def remove(self, index, *args, **kw):
        ''' Removes an object '''
        objects = self.get_list(index)
        objects.remove(*args, **kw)

    def all(self):
        ''' Returns all objects from all lists '''
        return (obj for objects in self for obj in objects)

    def metadata(self):
        return [objects.metadata() for objects in self]

    def template(self):
        return [objects.template() for objects in self]

    def __iter__(self):
        return iter(objects for objects in self._lists)

    def __len__(self):
        return len(self._lists)

    def __str__(self):
        s = []
        s.append('Objects:\n')
        for index, objects in enumerate(self):
            s.append('    {}# {}\n'.format(index, indent(str(objects), 4)))
        return '\n'.join(s)
