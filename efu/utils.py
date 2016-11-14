# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import shutil
import subprocess
from collections import OrderedDict

from jsonschema import Draft4Validator, FormatChecker, RefResolver


SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

# Environment variables (only for testing)
CHUNK_SIZE_VAR = 'EFU_CHUNK_SIZE'
GLOBAL_CONFIG_VAR = 'EFU_GLOBAL_CONFIG'
LOCAL_CONFIG_VAR = 'EFU_LOCAL_CONFIG'
SERVER_URL_VAR = 'EFU_SERVER_URL'

# Default values
DEFAULT_CHUNK_SIZE = 1024 * 128  # 128 KiB
DEFAULT_GLOBAL_CONFIG_FILE = os.path.expanduser('~/.efu')
DEFAULT_LOCAL_CONFIG_FILE = '.efu'
DEFAULT_SERVER_URL = 'http://0.0.0.0'  # TO DO: replace by the right URL


def get_chunk_size():
    return int(os.environ.get(CHUNK_SIZE_VAR, DEFAULT_CHUNK_SIZE))


def get_server_url(path=None):
    url = os.environ.get(SERVER_URL_VAR, DEFAULT_SERVER_URL).strip('/')
    if path is not None:
        url = ''.join((url, path))
    return url


def get_global_config_file():
    return os.environ.get(GLOBAL_CONFIG_VAR, DEFAULT_GLOBAL_CONFIG_FILE)


def get_local_config_file():
    return os.environ.get(LOCAL_CONFIG_VAR, DEFAULT_LOCAL_CONFIG_FILE)


def get_local_config():
    with open(get_local_config_file()) as fp:
        return json.load(fp, object_pairs_hook=OrderedDict)


def remove_local_config():
    os.remove(get_local_config_file())


def validate_schema(schema_fn, obj):
    base_uri = 'file://{}/'.format(SCHEMAS_DIR)
    with open(os.path.join(SCHEMAS_DIR, schema_fn)) as fp:
        schema = json.load(fp)
    resolver = RefResolver(base_uri, schema)
    format_checker = FormatChecker(formats=['uri'])
    validator = Draft4Validator(
        schema, resolver=resolver, format_checker=format_checker)
    validator.validate(obj)


def call(obj, name, *args, **kw):
    f = getattr(obj, name, lambda *args, **kw: None)
    f(*args, **kw)


# String utilities

def yes_or_no(value):
    '''
    Helper function to humanize boolean values.
    If value represents a True value, returns "yes", otherwise "no".
    '''
    if value:
        return 'yes'
    return 'no'


def str_wrapper(value, start='"', end='"'):
    '''
    Helper function to wrap a string between two strings.
    '''
    return '{}{}{}'.format(start, value, end)


def indent(value, n, all_lines=False):
    '''
    Indent a multline string to right by n.

    If all_lines is set to True, the first line will also be indeted,
    otherwise, first line will be 0 padded. This is so since we can
    attach the generated string in an already indented line.
    '''
    lines = value.split('\n')
    padding = n * ' '
    lines = ['{}{}'.format(padding, line).rstrip() for line in lines]
    text = '\n'.join(lines)
    if all_lines:
        return text
    return text.strip()


# Compressed file utilities

COMPRESSORS = {
    # GZIP format: http://www.gzip.org/zlib/rfc-gzip.html#file-format
    'gzip': {
        'signature': b'\x1f\x8b',
        'test': 'gzip -t %s',
        'cmd': "gzip -l %s | tail -n 1 | awk '{ print $2}'"
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
    '''
    If file is compressed and we support it, return compression
    format, otherwise return None explicitly.
    '''
    with open(fn, 'rb') as fp:
        header = fp.read(MAX_COMPRESSOR_SIGNATURE_SIZE)
    for fmt, compressor in COMPRESSORS.items():
        signature = compressor['signature']
        if signature == header[:len(signature)]:
            return fmt
    return None


def is_compressor_supported(compressor):
    '''
    Checks if compressor utility exists so we can get uncompressed
    size.
    '''
    return bool(shutil.which(compressor))


def is_valid_compressed_file(fn, compressor_name):
    ''' Checks if compressed file is a valid one. '''
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
    '''
    Returns uncompressed size of a given compressed file.
    '''
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
