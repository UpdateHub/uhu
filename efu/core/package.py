# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..metadata import PackageMetadata
from ..utils import get_package_file

from . import Object


class Package:

    def __init__(self, version):
        self.filename = get_package_file()

        with open(self.filename) as fp:
            self._package = json.load(fp)

        self.product = self._package.get('product')
        self.version = version

        self.objects = {}
        for fn, options in self._package.get('objects').items():
            obj = Object(fn, options)
            self.objects[obj.filename] = obj

        self.metadata = PackageMetadata(
            self.product, self.version, self.objects.values())

    def serialize(self):
        return {
            'version': self.version,
            'objects': [obj.serialize() for obj in self.objects.values()],
            'metadata': self.metadata.serialize()
        }
