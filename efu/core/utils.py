# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
from copy import deepcopy

from ..utils import get_local_config_file


VOLATILE_PACKAGE_OPTIONS = (
    'version',
)

VOLATILE_IMAGE_OPTIONS = (
    'size',
    'sha256sum',
)


def load_package():
    package_fn = get_local_config_file()
    with open(package_fn) as fp:
        package = json.load(fp)
    return package


def write_package(data):
    package_fn = get_local_config_file()
    with open(package_fn, 'w') as fp:
        json.dump(data, fp)


def create_package_from_metadata(metadata):
    try:
        package = load_package()
        if len(package.keys()) > 1:
            raise FileExistsError('Package file cannot be overwritten')
    except FileNotFoundError:
        # It is not a problem, we are going to create one
        pass

    package = deepcopy(metadata)
    images = package.pop('images', [])

    # Removes all volatile options within metadata
    for package_option in VOLATILE_PACKAGE_OPTIONS:
        try:
            del package[package_option]
        except KeyError:
            pass  # option not present

    # Removes all volatile options within images
    for image in images:
        for image_option in VOLATILE_IMAGE_OPTIONS:
            try:
                del image[image_option]
            except KeyError:
                pass  # option not present

    package['objects'] = images
    with open(get_local_config_file(), 'w') as fp:
        json.dump(package, fp)
    return package
