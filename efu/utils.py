# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
from collections import OrderedDict


_DEFAULT_CHUNK_SIZE = 1024 * 1024 * 5  # 5 MiB
_SERVER_URL = 'http://0.0.0.0'  # must be replaced by the right URL
_PACKAGE_FILE = '.efu'

DEFAULT_LOCAL_CONFIG_FILE = '.efu'
LOCAL_CONFIG_VAR = 'EFU_LOCAL_CONFIG'


def get_chunk_size():
    return int(os.environ.get('EFU_CHUNK_SIZE', _DEFAULT_CHUNK_SIZE))


def get_server_url(path=None):
    url = os.environ.get('EFU_SERVER_URL', _SERVER_URL)
    if path is not None:
        url = ''.join((url, path))
    return url


def get_package_file():
    return os.environ.get('EFU_PACKAGE_FILE', _PACKAGE_FILE)


def get_local_config_file():
    return os.environ.get(LOCAL_CONFIG_VAR, DEFAULT_LOCAL_CONFIG_FILE)


def get_local_config():
    with open(get_local_config_file()) as fp:
        return json.load(fp, object_pairs_hook=OrderedDict)


def yes_or_no(value):
    if value:
        return 'yes'
    return 'no'
