# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ._base import BaseObject


class CopyObject(BaseObject):
    mode = 'copy'
    allow_compression = True
    allow_install_condition = True
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-device',
        'target-path',
        'filesystem',
        'mount-options',
        'format?',
        'format-options',
    ]
    required_options = [
        'filename',
        'target-device',
        'target-path',
        'filesystem',
    ]
    requirements = [
        ('format?', 'format-options', True)
    ]
    string_template = [
        ('target-device', ('filesystem',)),
        ('format?', ('format-options',)),
        ('mount-options', ()),
        ('target-path', ())
    ]


class FlashObject(BaseObject):
    mode = 'flash'
    allow_compression = False
    allow_install_condition = True
    options = [
        'filename',
        'sha256sum',
        'size',
        'target-device',
    ]
    required_options = [
        'filename',
        'target-device',
    ]
    string_template = [
        ('target-device', ()),
    ]


class IMXKobsObject(BaseObject):
    mode = 'imxkobs'
    allow_compression = False
    allow_install_condition = True
    options = [
        'filename',
        'size',
        'sha256sum',
        '1k_padding',
        'search_exponent',
        'chip_0_device_path',
        'chip_1_device_path',
    ]
    required_options = [
        'filename',
    ]
    string_template = [
        ('1k_padding', ()),
        ('search_exponent', ()),
        ('chip_0_device_path', ()),
        ('chip_1_device_path', ()),
    ]


class RawObject(BaseObject):
    mode = 'raw'
    allow_compression = True
    allow_install_condition = True
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-device',
        'chunk-size',
        'count',
        'seek',
        'skip',
        'truncate',
    ]
    required_options = [
        'filename',
        'target-device',
    ]
    string_template = [
        ('target-device', ('seek', 'truncate')),
        ('chunk-size', ()),
        ('skip', ()),
        ('count', ()),
    ]


class TarballObject(BaseObject):
    mode = 'tarball'
    allow_compression = False
    allow_install_condition = False
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-device',
        'target-path',
        'filesystem',
        'mount-options',
        'format?',
        'format-options',
    ]
    required_options = [
        'filename',
        'target-device',
        'target-path',
        'filesystem',
    ]
    string_template = [
        ('target-device', ('filesystem',)),
        ('format?', ('format-options',)),
        ('mount-options', ()),
        ('target-path', ())
    ]


class UBIFSObject(BaseObject):
    mode = 'ubifs'
    allow_compression = True
    allow_install_condition = False
    options = [
        'filename',
        'size',
        'sha256sum',
        'volume',
    ]
    required_options = [
        'filename',
        'volume',
    ]
    string_template = [
        ('volume', ()),
    ]
