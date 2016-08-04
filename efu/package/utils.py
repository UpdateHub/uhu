# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from ..utils import get_package_file
from .exceptions import DotEfuExistsError, DotEfuDoesNotExistError


def create_efu_file(product, version):
    package = get_package_file()
    if os.path.exists(package):
        raise DotEfuExistsError
    with open(package, 'w') as fp:
        obj = {
            'product': product,
            'version': version
        }
        json.dump(obj, fp)


def add_image(filename, options):
    package = get_package_file()
    try:
        with open(package) as fp:
            dot_efu = json.load(fp)
    except FileNotFoundError:
        raise DotEfuDoesNotExistError

    options['install-mode'] = options['install_mode'].name
    del options['install_mode']

    files = dot_efu.get('files', {})
    files[filename] = options

    dot_efu['files'] = files

    with open(package, 'w') as fp:
        json.dump(dot_efu, fp)
