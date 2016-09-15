# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..metadata import PackageMetadata

from . import Object


class Package:

    def __init__(self, version=None, objects=None, product=None):
        self.version = version
        self.objects = objects if objects is not None else {}
        self.product = product
        self.metadata = None

    @classmethod
    def from_file(cls, fn):
        with open(fn) as fp:
            package = json.load(fp)

        file_objects = package.get('objects')
        product = package.get('product')
        version = package.get('version')
        objects = {}
        if file_objects is not None:
            for fn, options in file_objects.items():
                obj = Object(fn, options)
                objects[obj.filename] = obj
        package = Package(version=version, objects=objects, product=product)
        package.load_metadata()
        return package

    def load_metadata(self):
        self.metadata = PackageMetadata(
            self.product, self.version, self.objects.values())

    def serialize(self):
        return {
            'version': self.version,
            'objects': [obj.serialize() for obj in self.objects.values()],
            'metadata': self.metadata.serialize()
        }
