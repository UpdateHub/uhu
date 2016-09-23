# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
from collections import OrderedDict

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
