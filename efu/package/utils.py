# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from .exceptions import DotEfuExistsError, DotEfuDoesNotExistError


EFU_FILE = '.efu'


def create_efu_file(product, version):
    if os.path.exists(EFU_FILE):
        raise DotEfuExistsError
    with open(EFU_FILE, 'w') as fp:
        obj = {
            'product': product,
            'version': version
        }
        json.dump(obj, fp)


def add_image(filename, options):
    try:
        with open(EFU_FILE) as fp:
            dot_efu = json.load(fp)
    except FileNotFoundError:
        raise DotEfuDoesNotExistError

    options['install-mode'] = options['install_mode'].name
    del options['install_mode']

    files = dot_efu.get('files', {})
    files[filename] = options

    dot_efu['files'] = files

    with open(EFU_FILE, 'w') as fp:
        json.dump(dot_efu, fp)
