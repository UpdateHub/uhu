# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import shutil
import subprocess


COMPRESSORS = {
    # GZIP format: http://www.gzip.org/zlib/rfc-gzip.html#file-format
    'gzip': {
        'signature': b'\x1f\x8b',
        'test': 'gzip -t %s',
        # gzip requires -f if pigz is used.
        'cmd': "gzip -lf %s | tail -n 1 | awk '{ print $2}'"
    },
    # LZO format: http://www.lzop.org/download/lzop-1.03.tar.gz
    'lzop': {
        'signature': b'\x89LZO\x00\r\n\x1a\n',
        'test': 'lzop -t %s',
        'cmd': "lzop -l %s | tail -n 1 | awk '{ print $3}'"
    },
    # XZ format: http://tukaani.org/xz/xz-file-format.txt
    'xz': {
        'signature': b'\xfd7zXZ\x00',
        'test': 'xz -t %s',
        'cmd': "xz -l %s --robot | tail -n 1 | awk '{ print $5}'"
    },
}


MAX_COMPRESSOR_SIGNATURE_SIZE = max(
    [len(compressor['signature']) for compressor in COMPRESSORS.values()])


def get_compressor_format(fn):
    """Returns the compression backend for a given file.

    If file is compressed and we support it, return compression
    format, otherwise return None explicitly.
    """
    with open(fn, 'rb') as fp:
        header = fp.read(MAX_COMPRESSOR_SIGNATURE_SIZE)
    for fmt, compressor in COMPRESSORS.items():
        signature = compressor['signature']
        if signature == header[:len(signature)]:
            return fmt
    return None


def is_compressor_supported(compressor):
    """Checks if compressor utility exists.

    This is necessary so we can get the uncompressed size of an
    object.
    """
    return bool(shutil.which(compressor))


def is_valid_compressed_file(fn, compressor_name):
    """Checks if compressed file is a valid one."""
    compressor = COMPRESSORS.get(compressor_name)
    test_cmd = compressor['test'] % fn
    try:
        result = subprocess.check_call(test_cmd, shell=True)
        if result == 0:
            return True
    except subprocess.CalledProcessError:
        pass  # file is corrupted
    return False


def get_uncompressed_size(fn, compressor_name):
    """Returns uncompressed size of a given compressed file."""
    if compressor_name is None:
        return  # It is not a compressed file
    compressor = COMPRESSORS.get(compressor_name)
    if compressor is None:
        err = '"{}" is not supported'
        raise ValueError(err.format(compressor_name))
    if not is_compressor_supported(compressor_name):
        err = '"{}" is not supported by your system.'
        raise SystemError(err.format(compressor_name))
    if not is_valid_compressed_file(fn, compressor_name):
        err = '"{}" is a bad/corrupted {} file.'
        raise ValueError(err.format(fn, compressor_name))
    cmd = compressor['cmd'] % fn
    size = subprocess.check_output(cmd, shell=True)
    return int(size.decode())


def compression_to_metadata(filename):
    compressor = get_compressor_format(filename)
    size = get_uncompressed_size(filename, compressor)
    if size is None:
        return {}
    return {
        'compressed': True,
        'required-uncompressed-size': size,
    }
