# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..utils import get_package_file
from . import exceptions
from .object import Object
from .utils import is_metadata_valid


class Package(object):

    def __init__(self, version):
        self.file = get_package_file()
        self._package = self._validate_package(self.file)
        self.product_id = self._package.get('product')
        self.version = version
        self.objects = {}
        for fn, options in self._package.get('objects').items():
            obj = Object(fn, options)
            self.objects[obj.filename] = obj

    def _validate_package(self, fn):
        try:
            with open(fn) as fp:
                package = json.load(fp)
        except FileNotFoundError:
            raise exceptions.InvalidPackageObjectError(
                '{} file does not exist'.format(fn)
            )
        except ValueError:
            raise exceptions.InvalidPackageObjectError(
                '{} is not a valid JSON file'.format(fn)
            )
        return package

    def serialize(self):
        return {
            'version': self.version,
            'objects': [obj.serialize() for obj in self.objects.values()],
            'metadata': self.metadata
        }

    @property
    def metadata(self):
        objects = []
        for obj in self.objects.values():
            obj.load()
            objects.append(obj.metadata.serialize())
        metadata = {
            'product': self.product_id,
            'version': self.version,
            'images': objects
        }
        if is_metadata_valid(metadata):
            return metadata
        raise exceptions.InvalidMetadataError
