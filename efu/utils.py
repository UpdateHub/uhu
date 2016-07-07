# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

_DEFAULT_CHUNK_SIZE = 1024 * 1024 * 5  # 5 MiB
_SERVER_URL = 'http://0.0.0.0'  # must be replaced by the right URL


def get_chunk_size():
    chunk_size = _DEFAULT_CHUNK_SIZE
    return int(os.environ.get('EFU_CHUNK_SIZE', chunk_size))


def get_server_url(path=None):
    url = os.environ.get('EFU_SERVER_URL', _SERVER_URL)
    if path is not None:
        url = ''.join((url, path))
    return url
