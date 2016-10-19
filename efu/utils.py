# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import subprocess
from collections import OrderedDict

import magic
from jsonschema import Draft4Validator, FormatChecker, RefResolver


SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

# Environment variables (only for testing)
CHUNK_SIZE_VAR = 'EFU_CHUNK_SIZE'
GLOBAL_CONFIG_VAR = 'EFU_GLOBAL_CONFIG'
LOCAL_CONFIG_VAR = 'EFU_LOCAL_CONFIG'
SERVER_URL_VAR = 'EFU_SERVER_URL'

# Default values
DEFAULT_CHUNK_SIZE = 1024 * 1024 * 5  # 5 MiB
DEFAULT_GLOBAL_CONFIG_FILE = os.path.expanduser('~/.efu')
DEFAULT_LOCAL_CONFIG_FILE = '.efu'
DEFAULT_SERVER_URL = 'http://0.0.0.0'  # TO DO: replace by the right URL


def get_chunk_size():
    return int(os.environ.get(CHUNK_SIZE_VAR, DEFAULT_CHUNK_SIZE))


def get_server_url(path=None):
    url = os.environ.get(SERVER_URL_VAR, DEFAULT_SERVER_URL)
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


def yes_or_no(value):
    if value:
        return 'yes'
    return 'no'


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


# Compressed file utilities

SUPPORTED_COMPRESSION_MIMES = [
    'application/gzip',
    'application/x-gzip',
    'application/x-xz'
]


def get_uncompressed_size(fn):
    mime = magic.from_file(fn, mime=True)
    try:
        f = {
            'application/x-gzip': gzip_uncompressed_size,
            'application/gzip': gzip_uncompressed_size,
            'application/x-xz': lzma_uncompressed_size,
            'application/octet-stream': lzo_uncompressed_size,
        }[mime]
        return f(fn)
    except KeyError:
        raise ValueError('Unsuported compressed file type')


def is_compression_supported(fn):
    # This will only work if file exists (uploads)
    mime = magic.from_file(fn, mime=True)
    if mime in SUPPORTED_COMPRESSION_MIMES:
        return True
    if mime == 'application/octet-stream' and is_lzo(fn):
        return True
    return False


def gzip_uncompressed_size(fn):
    if is_gzip(fn):
        cmd = "gzip -l %s | tail -n 1 | awk '{ print $2}'"
        size = subprocess.check_output(cmd % fn, shell=True)
        return int(size.decode())


def lzma_uncompressed_size(fn):
    if is_lzma(fn):
        cmd = "xz -l %s --robot | tail -n 1 | awk '{ print $5}'"
        size = subprocess.check_output(cmd % fn, shell=True)
        return int(size.decode())


def lzo_uncompressed_size(fn):
    if is_lzo(fn):
        cmd = "lzop -l %s | tail -n 1 | awk '{ print $3}'"
        size = subprocess.check_output(cmd % fn, shell=True)
        return int(size.decode())


def is_lzo(fn):
    result = subprocess.call(['lzop', '-t', fn])
    return not bool(result)


def is_lzma(fn):
    result = subprocess.call(['xz', '-t', fn])
    return not bool(result)


def is_gzip(fn):
    result = subprocess.call(['gzip', '-t', fn])
    return not bool(result)
