# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
from copy import deepcopy

from ..utils import get_local_config_file, yes_or_no


VOLATILE_PACKAGE_OPTIONS = (
    'version',
)

VOLATILE_IMAGE_OPTIONS = (
    'size',
    'sha256sum',
)

DEVICE_OPTIONS = ['truncate', 'seek', 'filesystem']


def load_package():
    package_fn = get_local_config_file()
    with open(package_fn) as fp:
        package = json.load(fp)
    return package


def write_package(data):
    package_fn = get_local_config_file()
    with open(package_fn, 'w') as fp:
        json.dump(data, fp)


def create_package_file(product):
    package_fn = get_local_config_file()
    if os.path.exists(package_fn):
        raise FileExistsError('Package file cannot be overwritten')
    package = {'product': product}
    write_package(package)


def add_image(filename, options):
    package = load_package()
    objects = package.get('objects', {})
    objects[filename] = options
    package['objects'] = objects
    write_package(package)


def remove_image(filename):
    package = load_package()
    del package['objects'][filename]
    write_package(package)


def list_images():
    ''' Prints current package content '''
    package = load_package()
    objects = package.get('objects')
    print('Product: {}'.format(package['product']))
    print()
    print('Images:')
    for file, options in objects.items():
        print()
        print('  {} [install mode: {}]'.format(file, options['install-mode']))
        print()
        # compressed option
        compressed = options.get('compressed')
        if compressed is not None:
            line = '      Compressed file:   {}'.format(yes_or_no(compressed))
            if compressed:
                line += ' [uncompressed size: {}B]'.format(
                    options.get('required-uncompressed-size'))
            print(line)
        # device option
        device = options.get('target-device')
        if device is not None:
            line = '      Target device:     {}'.format(device)
            device_options = {option: options.get(option)
                              for option in DEVICE_OPTIONS}
            if any(device_options.values()):
                truncate = device_options['truncate']
                if truncate is not None:
                    device_options['truncate'] = yes_or_no(truncate)
                device_options = ['{}: {}'.format(k, v)
                                  for k, v in device_options.items()
                                  if v is not None]
                line += ' [{}]'.format(', '.join(device_options))
            print(line)
        # format option
        format_ = options.get('format?')
        if format_ is not None:
            line = '      Format device:     {}'.format(
                yes_or_no(format_))
            format_options = options.get('format-options')
            if format_options:
                line += '[options: "{}"]'.format(format_options)
            print(line)
        # mount options
        mount = options.get('mount-options')
        if mount is not None:
            print('      Mount options:     "{}"'.format(mount))
        # target path option
        path = options.get('target-path')
        if path is not None:
            print('      Target path:       {}'.format(path))
        # chunk size option
        chunk = options.get('chunk-size')
        if chunk is not None:
            print('      Chunk size:        {}'.format(chunk))
        # skip option
        skip = options.get('skip')
        if skip is not None:
            print('      Skip from source:  {}'.format(skip))
        # count option
        count = options.get('count')
        if count is not None:
            print('      Count:             {}'.format(count))
    print()


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
