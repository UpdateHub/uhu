# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import re
import string
import struct
import zlib
from copy import deepcopy


# Utilities

PRINTABLE = string.printable.encode()
KNOWN_PATTERNS = ['linux-kernel', 'u-boot']
CUSTOM_PATTERN = 'regexp'


def read(fp, seek, type_, buffer_size):
    """Retrives a chunk from file and converts it to a given type."""
    fp.seek(seek)
    try:
        return struct.unpack(type_, fp.read(buffer_size))[0]
    except struct.error:
        return None


def check(phrase, regexp):
    """Checks if a phrase matches a given regexp pattern."""
    results = regexp.findall(phrase)
    if results:
        return results[0].decode()


def find(fp, pattern, iterable, seek=0):
    """Generic function to find some text in some iterable."""
    fp.seek(seek)
    regexp = re.compile(pattern)
    phrase = b''
    for chunk in iterable:
        for char in chunk:
            if char in PRINTABLE:
                phrase += bytes([char])
            else:
                result = check(phrase, regexp)
                if result:
                    return result
                phrase = b''
    return check(phrase, regexp)


# Linux Kernel utilities

ARM_Z_IMAGE = 0x016F2818
ARM_U_IMAGE = 0x27051956
X86_BZ_IMAGE = (0xaa55, 1)
X86_Z_IMAGE = (0xaa55, 0)


def is_arm_u_image(fp):
    """Checks if an image is ARM uImage."""
    return read(fp, 0, '>I', 4) == ARM_U_IMAGE


def is_arm_z_image(fp):
    """Checks if an image is ARM zImage."""
    return read(fp, 36, '<I', 4) == ARM_Z_IMAGE


def get_x86_generic_image_info(fp):
    """Generic function to retrive Linux kernel info from x86 images."""
    magic = read(fp, 510, '<H', 2)
    data = read(fp, 529, '<c', 1)
    compression = ord(data) if data is not None else None
    return (magic, compression)


def is_x86_bz_image(fp):
    """Checks if an image is x86 bzImage."""
    return get_x86_generic_image_info(fp) == X86_BZ_IMAGE


def is_x86_z_image(fp):
    """Checks if an image is x86 zImage."""
    return get_x86_generic_image_info(fp) == X86_Z_IMAGE


def get_arm_z_image_version(fp):
    """Returns Linux kernel version of an ARM zImage."""
    # In ARM uImage kernel is compressed within the image. To retrive
    # its version, we need find the compressed kernel, uncompress it,
    # and extract the version from the uncompressed data.

    fp.seek(0)
    # "0x1f 0x8b 0x08" is the beginning of the gzipped kernel file
    start = bytearray.fromhex('1f 8b 08 00 00 00 00 00')
    # This could be improved so we don't have to read all file in memory
    seek = fp.read().index(start)
    pattern = br'Linux version (\S+).*'
    decompressor = zlib.decompressobj(zlib.MAX_WBITS | 16)
    iterable = iter(lambda: decompressor.decompress(fp.read(30)), b'')
    return find(fp, pattern, iterable, seek)


def get_arm_u_image_version(fp):
    """Returns Linux kernel version of an ARM uImage."""
    fp.seek(32)
    data = fp.read(32).strip(b'\0')
    regexp = re.compile(br'(\d+.?\.[^\s]+)')
    version = check(data, regexp)
    return version


def get_x86_generic_version(fp):
    """Retrives Linux kernel version from x86 images."""
    offset = read(fp, 526, '<H', 2)
    fp.seek(offset + 512)  # 0x200
    version = fp.read(512)
    regexp = re.compile(br'(\d+.?\.[^\s]+)')
    return check(version, regexp)


def get_x86_bz_image_version(fp):
    """Returns Linux kernel version of a x86 bzImage."""
    return get_x86_generic_version(fp)


def get_x86_z_image_version(fp):
    """Returns Linux kernel version of a x86 zImage."""
    return get_x86_generic_version(fp)


# Linux Kernel

def get_kernel_version(fp):
    """Returns Linux kernel object version."""
    result = None
    # ARM uImage
    if is_arm_u_image(fp):
        result = get_arm_u_image_version(fp)
    # ARM zImage
    if is_arm_z_image(fp):
        result = get_arm_z_image_version(fp)
    # x86 bzImage
    if is_x86_bz_image(fp):
        result = get_x86_bz_image_version(fp)
    # x86 zImage
    if is_x86_z_image(fp):
        result = get_x86_z_image_version(fp)
    if result is not None:
        return result
    raise ValueError('Cannot retrive kernel version')


# U-Boot

def get_uboot_version(fp):
    """Returns U-Boot object version."""
    pattern = br'U-Boot(?: SPL)? (\S+) \(.*\)'
    iterable = iter(lambda: fp.read(30), b'')
    result = find(fp, pattern, iterable, 0)
    if result is not None:
        return result
    raise ValueError('Cannot retrive U-Boot version')


# Arbitrary object

def get_object_version(fp, pattern, seek=0, buffer_size=-1):
    """Returns version of any type of object."""
    iterable = iter(lambda: fp.read(buffer_size), b'')
    result = find(fp, pattern, iterable, seek)
    if result is not None:
        return result
    raise ValueError('Cannot retrive object version')


def get_version(fn, type_, **kwargs):
    with open(fn, 'rb') as fp:
        if type_ == 'linux-kernel':
            return get_kernel_version(fp)
        elif type_ == 'u-boot':
            return get_uboot_version(fp)
        elif type_ == 'regexp':
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            return get_object_version(fp, **kwargs)


def normalize_install_if_different(values):
    """Converts metadata install-if-different key to install-condition."""
    values = deepcopy(values)
    iid = values.pop('install-if-different', None)

    # Without install-if-different
    if iid is None:
        return values

    # Content diverges
    if iid == 'sha256sum':
        values.update({'install-condition': 'content-diverges'})
        return values

    if not isinstance(iid, dict):
        raise TypeError('Cannot parse install if different.')

    version = iid.get('version')
    if version is None:
        raise ValueError('Missing version in install-if-different property.')

    # Known pattern
    pattern = iid.get('pattern')
    if pattern in KNOWN_PATTERNS:
        values.update({
            'install-condition': 'version-diverges',
            'install-condition-version': version,
            'install-condition-pattern-type': pattern,
        })
        return values

    # Custom pattern
    regexp = pattern.get('regexp')
    if regexp is None:
        raise ValueError('Missing regexp in install-if-different property.')
    # TODO: validate seek and buffer-size
    values.update({
        'install-condition': 'version-diverges',
        'install-condition-version': version,
        'install-condition-pattern-type': 'regexp',
        'install-condition-pattern': regexp,
        'install-condition-seek': pattern.get('seek', 0),
        'install-condition-buffer-size': pattern.get('buffer-size', -1),
    })
    return values


class InstallCondition:  # pylint: disable=too-few-public-methods
    METADATA_KEY = 'install-if-different'

    # Conditions
    ALWAYS = 'always'
    CONTENT_DIVERGES = 'content-diverges'
    VERSION_DIVERGES = 'version-diverges'

    def __init__(self, metadata):
        self.filename = metadata['filename']
        self.condition = metadata.pop('install-condition', None)
        self.metadata = metadata
        self.pattern = None

    def to_metadata(self):
        if self.condition == self.CONTENT_DIVERGES:
            return self._format_metadata('sha256sum')
        elif self.condition == self.VERSION_DIVERGES:
            return self._metadata_version_diverges()
        elif self.condition == self.ALWAYS:
            return {}
        raise ValueError('Invalid install-condition condition.')

    def _metadata_version_diverges(self):
        self.pattern = self.metadata.pop(
            'install-condition-pattern-type', None)
        if self.pattern in KNOWN_PATTERNS:
            return self._metadata_known_pattern()
        elif self.pattern == CUSTOM_PATTERN:
            return self._metadata_custom_pattern()
        raise ValueError('Unknown install-condition pattern type.')

    def _metadata_known_pattern(self):
        return self._format_metadata({
            'pattern': self.pattern,
            'version': get_version(self.filename, self.pattern),
        })

    def _metadata_custom_pattern(self):
        regexp = self.metadata.pop('install-condition-pattern')
        seek = self.metadata.pop('install-condition-seek')
        buffer_size = self.metadata.pop('install-condition-buffer-size')
        version = get_version(
            self.filename, CUSTOM_PATTERN, pattern=regexp.encode(),
            seek=seek, buffer_size=buffer_size)
        return self._format_metadata({
            'version': version,
            'pattern': {
                'buffer-size': buffer_size,
                'regexp': regexp,
                'seek': seek,
            },
        })

    def _format_metadata(self, value):
        return {self.METADATA_KEY: value}
