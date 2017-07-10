# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from ._object import BaseObject


class CopyObject(BaseObject):
    mode = 'copy'
    allow_compression = True
    allow_install_condition = True
    target_types = ['device']
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-type',
        'target',
        'target-path',
        'filesystem',
        'mount-options',
        'format?',
        'format-options',
    ]
    required_options = [
        'filename',
        'target-type',
        'target',
        'target-path',
        'filesystem',
    ]
    requirements = [
        ('format?', 'format-options', True)
    ]
    string_template = [
        ('target', ('filesystem',)),
        ('format?', ('format-options',)),
        ('mount-options', ()),
        ('target-path', ())
    ]


class FlashObject(BaseObject):
    mode = 'flash'
    allow_compression = False
    allow_install_condition = True
    target_types = ['device', 'mtdname']
    options = [
        'filename',
        'sha256sum',
        'size',
        'target-type',
        'target',
    ]
    required_options = [
        'filename',
        'target-type',
        'target',
    ]
    string_template = [
        ('target', ()),
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
    target_types = ['device']
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-type',
        'target',
        'chunk-size',
        'count',
        'seek',
        'skip',
        'truncate',
    ]
    required_options = [
        'filename',
        'target-type',
        'target',
    ]
    string_template = [
        ('target', ('seek', 'truncate')),
        ('chunk-size', ()),
        ('skip', ()),
        ('count', ()),
    ]


class TarballObject(BaseObject):
    mode = 'tarball'
    allow_compression = False
    allow_install_condition = False
    target_types = ['device', 'mtdname', 'ubivolume']
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-type',
        'target',
        'target-path',
        'filesystem',
        'mount-options',
        'format?',
        'format-options',
    ]
    required_options = [
        'filename',
        'target-type',
        'target',
        'target-path',
        'filesystem',
    ]
    string_template = [
        ('target', ('filesystem',)),
        ('format?', ('format-options',)),
        ('mount-options', ()),
        ('target-path', ())
    ]


class UBIFSObject(BaseObject):
    mode = 'ubifs'
    allow_compression = True
    allow_install_condition = False
    target_types = ['ubivolume']
    options = [
        'filename',
        'size',
        'sha256sum',
        'target-type',
        'target',
    ]
    required_options = [
        'filename',
        'target-type',
        'target',
    ]
    string_template = [
        ('target', ()),
    ]
