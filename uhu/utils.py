# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import base64
import json
import os

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


# Environment variables
CHUNK_SIZE_VAR = 'UHU_CHUNK_SIZE'
GLOBAL_CONFIG_VAR = 'UHU_GLOBAL_CONFIG'
LOCAL_CONFIG_VAR = 'UHU_LOCAL_CONFIG'
SERVER_URL_VAR = 'UHU_SERVER_URL'
ACCESS_ID_VAR = 'UHU_ACCESS_ID'
ACCESS_SECRET_VAR = 'UHU_ACCESS_SECRET'
PRIVATE_KEY_FN = 'UHU_PRIVATE_KEY'
CUSTOM_CA_CERTS_VAR = 'UHU_CUSTOM_CA_CERTS'


# Default values
DEFAULT_CHUNK_SIZE = 1024 * 128  # 128 KiB
DEFAULT_GLOBAL_CONFIG_FILE = os.path.expanduser('~/.uhu')
DEFAULT_LOCAL_CONFIG_FILE = '.uhu'
DEFAULT_SERVER_URL = 'http://0.0.0.0'  # TODO: replace by the right URL


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


def get_credentials():
    access = os.environ.get(ACCESS_ID_VAR)
    secret = os.environ.get(ACCESS_SECRET_VAR)
    if access and secret:
        return access, secret


def get_custom_ca_certs_file():
    return os.environ.get(CUSTOM_CA_CERTS_VAR, None)


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


def list_to_str(title, lst):
    """Given a title and a list prints a named ordered list.

    Ex. title=Menu and lst=[eggs, spam] gives:

        Menu:
            0# eggs
            1# spam
    """
    lines = ['{}:'.format(title)]
    for index, elm in enumerate(lst):
        line = '    {}# {}'.format(index, indent(elm, 4))
        lines.append('')
        lines.append(line)
    return '\n'.join(lines)


def sign_dict(dict_, private_key):
    """Serializes a dict to JSON and sign it using RSA."""
    try:
        with open(private_key) as fp:
            key = RSA.importKey(fp.read())
    except (FileNotFoundError, ValueError, IndexError, TypeError):
        raise ValueError('Invalid private key file.')

    signer = PKCS1_v1_5.new(key)

    # encodes message
    message = SHA256.new(json.dumps(dict_, sort_keys=True).encode())

    # sign
    signature = signer.sign(message)
    return base64.b64encode(signature).decode()
