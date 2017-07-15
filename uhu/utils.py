# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os


# Environment variables (only for testing)
CHUNK_SIZE_VAR = 'UHU_CHUNK_SIZE'
GLOBAL_CONFIG_VAR = 'UHU_GLOBAL_CONFIG'
LOCAL_CONFIG_VAR = 'UHU_LOCAL_CONFIG'
SERVER_URL_VAR = 'UHU_SERVER_URL'

# Default values
DEFAULT_CHUNK_SIZE = 1024 * 128  # 128 KiB
DEFAULT_GLOBAL_CONFIG_FILE = os.path.expanduser('~/.uhu')
DEFAULT_LOCAL_CONFIG_FILE = '.uhu'
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


def remove_local_config():
    os.remove(get_local_config_file())


def call(obj, name, *args, **kw):
    func = getattr(obj, name, lambda *args, **kw: None)
    func(*args, **kw)


def indent(value, n_indents, all_lines=False):
    """Indent a multline string to right by n_indents.

    If all_lines is set to True, the first line will also be indented,
    otherwise, first line will be 0 padded. This is so since we can
    attach the generated string in an already indented line.
    """
    lines = value.split('\n')
    padding = n_indents * ' '
    lines = ['{}{}'.format(padding, line).rstrip() for line in lines]
    text = '\n'.join(lines)
    if all_lines:
        return text
    return text.strip()
