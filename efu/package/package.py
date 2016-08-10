# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..utils import get_package_file
from . import exceptions
from .file import File
from .utils import is_metadata_valid


class Package(object):

    def __init__(self, version):
        self.file = get_package_file()
        self._package = self._validate_package(self.file)
        self.product_id = self._package.get('product')
        self.version = version
        self.files = {}
        for fn, options in self._package.get('files').items():
            file = File(fn, options)
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
            'objects': [file.as_dict() for file in self.files.values()],
            'metadata': self.metadata
        }

    @property
    def metadata(self):
        metadata = {
            'product': self.product_id,
            'version': self.version,
            'images': [file.metadata for file in self.files.values()]
        }
        if is_metadata_valid(metadata):
            return metadata
        raise exceptions.InvalidMetadataError
