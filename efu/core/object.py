# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import json
import math
import os
from collections import OrderedDict
from copy import deepcopy

import requests
from humanize.filesize import naturalsize

from ..exceptions import DownloadError, UploadError
from ..http import Request
from ..utils import (
    call, get_chunk_size, get_server_url, get_uncompressed_size,
    get_compressor_format, yes_or_no, str_wrapper)

from .install_condition import (
    get_kernel_version, get_uboot_version, get_object_version)
from .options import OptionsParser, INSTALL_CONDITION_BACKENDS
from .storages import STORAGES


OBJECT_STRING_TEMPLATE = OrderedDict([
    ('volume', OrderedDict([
        ('display', 'Volume name:')
    ])),
    ('1k_padding', OrderedDict([
        ('display', 'Add 1k-padding in the head:'),
        ('formatter', yes_or_no),
    ])),
    ('search_exponent', OrderedDict([
        ('display', 'Search exponent:')
    ])),
    ('chip_0_device_path', OrderedDict([
        ('display', 'Chip-0 device path:')
    ])),
    ('chip_1_device_path', OrderedDict([
        ('display', 'Chip-1 device path:')
    ])),
    ('target-device', OrderedDict([
        ('display', 'Target device:'),
        ('children', OrderedDict([
            ('seek', OrderedDict([
                ('display', 'seek:'),
            ])),
            ('truncate', OrderedDict([
                ('display', 'truncate:'),
                ('formatter', yes_or_no),
            ])),
            ('filesystem', OrderedDict([
                ('display', 'filesystem:'),
            ])),
        ])),
    ])),
    ('format?', OrderedDict([
        ('display', 'Format device:'),
        ('formatter', yes_or_no),
        ('children', OrderedDict([
            ('format-options', OrderedDict([
                ('display', 'options:'),
                ('formatter', str_wrapper),
            ])),
        ])),
    ])),
    ('mount-options', OrderedDict([
        ('display', 'Mount options:'),
        ('formatter', str_wrapper),
    ])),
    ('target-path', OrderedDict([
        ('display', 'Target path:'),
    ])),
    ('chunk-size', OrderedDict([
        ('display', 'Chunk size:'),
        ('formatter', lambda value: naturalsize(value, binary=True)),
    ])),
    ('skip', OrderedDict([
        ('display', 'Skip from source:'),
    ])),
    ('count', OrderedDict([
        ('display', 'Count:'),
        ('formatter', lambda value: 'all content' if value == -1 else value)
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
    """Represents an object to be deployed on agent.

    In other words, it is a file or a image with instructions (metadata)
    to agent install it on device.
    """

    VOLATILE_OPTIONS = ('size', 'sha256sum', 'required-uncompressed-size')
    DEVICE_OPTIONS = ['truncate', 'seek', 'filesystem']

    def __init__(self, fn, mode, options, sha256sum=None):
        self.filename = self.validate_filename(fn)
        self.mode = mode
        self.options = OptionsParser(self.mode, options).clean()

        self.install_condition = self._init_install_condition()

        self.size = None
        self.version = None
        self.md5 = None
        self.sha256sum = sha256sum

        self.chunk_size = get_chunk_size()

    def validate_filename(self, fn):
        """Validates if a given filename is not an invalid filename."""
        error_msg = '"{}" is not a valid filename.'.format(fn)
        if not isinstance(fn, str):
            raise TypeError(error_msg)
        if not fn:  # checks if filename is not an empty string
            raise ValueError(error_msg)
        return fn

    def _init_install_condition(self):
        """Retrives install-condition properties from object options."""
        condition = self.options.pop('install-condition', None)
        if condition is None:
            return None
        if condition in ['always', 'content-diverges']:
            return {'install-condition': condition}
        type_ = self.options.pop('install-condition-pattern-type')
        if type_ != 'regexp':
            return {
                'install-condition': condition,
                'install-condition-pattern-type': type_,
            }
        pattern = self.options.pop('install-condition-pattern', None)
        seek = self.options.pop('install-condition-seek', 0)
        buffer_size = self.options.pop('install-condition-buffer-size', -1)
        return {
            'install-condition': condition,
            'install-condition-pattern': pattern,
            'install-condition-pattern-type': type_,
            'install-condition-seek': seek,
            'install-condition-buffer-size': buffer_size,
        }

    @property
    def install_if_different(self):
        if self.install_condition is None:
            return None
        condition = self.install_condition.get('install-condition')
        if condition == 'always' or condition is None:
            iid = None
        elif condition == 'content-diverges':
            iid = 'sha256sum'
        elif condition == 'version-diverges':
            iid = {
                'version': self.install_condition['install-condition-version']
            }
            backend = self.install_condition['install-condition-pattern-type']
            if backend in INSTALL_CONDITION_BACKENDS:
                iid['pattern'] = backend
            else:
                iid['pattern'] = {
                    'regexp': self.install_condition['install-condition-pattern'],  # nopep8
                    'seek': self.install_condition['install-condition-seek'],
                    'buffer-size': self.install_condition['install-condition-buffer-size'],  # nopep8
                }
        return iid

    @classmethod
    def to_install_condition(cls, metadata):
        iid = metadata.get('install-if-different')
        if iid == 'sha256sum':
            return {'install-condition': 'content-diverges'}
        condition = {
            'install-condition': 'version-diverges',
        }
        pattern = iid.get('pattern')
        if pattern in ['linux-kernel', 'u-boot']:
            condition['install-condition-pattern-type'] = pattern
        else:
            condition['install-condition-pattern-type'] = 'regexp'
            condition['install-condition-pattern'] = pattern.get('regexp')
            condition['install-condition-seek'] = pattern.get('seek', 0)
            condition['install-condition-buffer-size'] = pattern.get('buffer-size', -1)  # nopep8
        return condition

    def get_uncompressed_size(self):
        """Returns object uncompressed size.

        If object mode supports compression, EFU supports compression
        format and object is not corrupted returns the uncompressed
        size, otherwise None.
        """
        # Modes which do not implement/supoprt compression:
        # - Copy object cannot be set as compressed since it can mislead user
        # when just copying a compressed file (instead of decompress
        # and copy).
        # - Flash object doesn't implement compression.
        # - imxkobs object doesn't implement compression.
        if self.mode not in ['copy', 'flash', 'imxkobs']:
            compressor = get_compressor_format(self.filename)
            return get_uncompressed_size(self.filename, compressor)

    def metadata(self):
        """Serialize object as metadata."""
        metadata = {
            'filename': self.filename,
            'mode': self.mode,
            'sha256sum': self.sha256sum,
            'size': self.size,
        }
        uncompressed_size = self.get_uncompressed_size()
        if uncompressed_size is not None:
            metadata['compressed'] = True
            metadata['required-uncompressed-size'] = uncompressed_size
        if self.install_if_different is not None:
            metadata['install-if-different'] = self.install_if_different
        metadata.update(self.options)
        return metadata

    def template(self):
        """Serialize object for dumping to a file."""
        options = deepcopy(self.options)
        if self.install_condition is not None:
            options.update(self.install_condition)
        options.pop('install-condition-version', None)

        template = {
            'filename': self.filename,
            'mode': self.mode,
            'options': options,
        }
        return template

    def update(self, option, value):
        """Updates an object option."""
        if option == 'filename':
            self.filename = self.validate_filename(value)
        else:
            options = deepcopy(self.options)
            options[option] = value
            self.options = OptionsParser(self.mode, options).clean()

    def load(self, cache=None, callback=None):
        """Reads object to set its size, sha256sum, MD5 and version."""
        cache = {} if cache is None else cache
        self.size = cache.get('size', os.path.getsize(self.filename))
        self.sha256sum = cache.get('sha256sum')
        self.md5 = cache.get('md5')
        if not all((self.sha256sum, self.md5)):
            sha256sum = hashlib.sha256()
            md5 = hashlib.md5()
            for chunk in self:
                sha256sum.update(chunk)
                md5.update(chunk)
                call(callback, 'object_read', self)
            self.sha256sum = sha256sum.hexdigest()
            self.md5 = md5.hexdigest()
        self.load_install_condition(cache)

    def load_install_condition(self, cache=None):
        cache = {} if cache is None else cache
        if self.install_condition is not None:
            self.version = cache.get('version', self.get_version())
            self.install_condition['install-condition-version'] = self.version

    def get_version(self):
        version_absent = ['always', 'content-diverges']
        if self.install_condition['install-condition'] in version_absent:
            return None
        with open(self.filename, 'rb') as fp:
            type_ = self.install_condition['install-condition-pattern-type']
            if type_ == 'linux-kernel':
                return get_kernel_version(fp)
            elif type_ == 'u-boot':
                return get_uboot_version(fp)
            elif type_ == 'regexp':
                pattern = self.install_condition['install-condition-pattern']
                return get_object_version(
                    fp,
                    pattern.encode(),
                    self.install_condition['install-condition-seek'],
                    self.install_condition['install-condition-buffer-size'],
                )

    def upload(self, product_uid, package_uid, callback=None):
        url = get_server_url('/products/{}/packages/{}/objects/{}'.format(
            product_uid, package_uid, self.sha256sum))
        body = json.dumps({'etag': self.md5})
        response = Request(url, 'POST', body, json=True).send()
        if response.status_code == 200:
            result = ObjectUploadResult.EXISTS
            call(callback, 'object_read', self, full=True)
        elif response.status_code == 201:
            body = response.json()
            upload = STORAGES[body['storage']]
            success = upload(self, body['url'], callback)
            if success:
                result = ObjectUploadResult.SUCCESS
            else:
                result = ObjectUploadResult.FAIL
        else:
            errors = response.json().get('errors', [])
            error_msg = 'It was not possible to get url:\n{}'
            raise UploadError(error_msg.format('\n'.join(errors)))
        return result

    def exists(self):
        return os.path.exists(self.filename)

    def download(self, url):
        if self.exists():
            return
        try:
            response = requests.get(url, stream=True)
        except requests.exceptions.ConnectionError:
            raise DownloadError('Can\'t reach the server.')
        if not response.ok:
            error_msg = 'It was not possible to download object:\n{}'
            raise DownloadError(error_msg.format(response.text))
        with open(self.filename, 'wb') as fp:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
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
        formatter = conf.get('formatter', False)
        if formatter:
            value = formatter(value)
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

    def _str_install_condition(self):
        s = []
        condition = self.install_condition.get('install-condition')
        if condition == 'always':
            s.append('    Install condition: always install')
        elif condition == 'content-diverges':
            s.append('    Install condition: install when CONTENT diverges')
        elif condition == 'version-diverges':
            s.append('    Install condition: install when VERSION diverges')
            type_ = self.install_condition['install-condition-pattern-type']
            if type_ == 'regexp':
                msg = '    Version pattern:   "{}" [seek: {}, buffer-size: {}]'
                s.append(msg.format(
                    self.install_condition['install-condition-pattern'],
                    self.install_condition['install-condition-seek'],
                    self.install_condition['install-condition-buffer-size'],
                ))
            else:
                s.append('    Version pattern:   linux-kernel')
        return '\n'.join(s)

    def __str__(self):
        s = []
        header = '{} [mode: {}]\n'.format(self.filename, self.mode)
        s.append(header)
        if self.install_condition is not None:
            s.append(self._str_install_condition())
        for option, conf in OBJECT_STRING_TEMPLATE.items():
            if option in self.options:
                value = self._str_value(option, conf)
                line = '    {:<18} {} {}'.format(
                    conf['display'], value, self._str_children(conf))
                s.append(line.rstrip())
        return '\n'.join(s)


class ObjectReader:
    """Read-only object class. Used when uploading with requests."""

    def __init__(self, obj, callback=None):
        self.obj = obj
        self.callback = callback

    def __len__(self):
        return os.path.getsize(self.obj.filename)

    def __iter__(self):
        for chunk in self.obj:
            call(self.callback, 'object_read', self.obj)
            yield chunk
