# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from .exceptions import DotEfuExistsError


def create_efu_file(product, version):
    if os.path.exists('.efu'):
        raise DotEfuExistsError
    with open('.efu', 'w') as fp:
        obj = {
            'product': product,
            'version': version
        }
        json.dump(obj, fp)
