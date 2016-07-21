# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from . import exceptions
from .file import File


class Package(object):

    def __init__(self, fn):
        self.file = fn
        self._package = self._validate_package(self.file)
        self.product_id = self._package.get('product_id')
        self.version = self._package.get('version')
        self.files = {}
        for fn in self._package.get('files'):
            file = File(fn)
            self.files[file.id] = file

    def _validate_package(self, fn):
        try:
            with open(fn) as fp:
                package = json.load(fp)
        except FileNotFoundError:
            raise exceptions.InvalidPackageFileError(
                '{} file does not exist'.format(fn)
            )
        except ValueError:
            raise exceptions.InvalidPackageFileError(
                '{} is not a valid JSON file'.format(fn)
            )
        return package

    def as_dict(self):
        return {
            'version': self.version,
            'objects': [file.as_dict() for file in self.files.values()]
        }
