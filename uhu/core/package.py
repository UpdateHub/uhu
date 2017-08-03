# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from uhu.updatehub.api import push_package
from uhu.utils import call

from .hardware import SupportedHardwareManager
from .objects import ObjectsManager


class Package:
    """A package represents a group of objects."""

    def __init__(self, version=None, product=None, dump=None):
        if dump is None:
            self.version = version
            self.product = product
            self.objects = ObjectsManager()
            self.supported_hardware = SupportedHardwareManager()
        else:
            self.version = dump.get('version')  # TODO: validate it
            self.product = dump.get('product')  # TODO: validate it
            self.objects = ObjectsManager(dump=dump)
            self.supported_hardware = SupportedHardwareManager(dump=dump)
        self.uid = None

    def to_metadata(self, callback=None):
        """Serialize package as metadata."""
        metadata = {
            'product': self.product,
            'version': self.version,
        }
        metadata.update(self.supported_hardware.to_metadata())
        metadata.update(self.objects.to_metadata(callback))
        return metadata

    def to_template(self, with_version=True):
        """Serialize package to dump to a file."""
        template = {'product': self.product}
        template['version'] = self.version if with_version else None
        template.update(self.objects.to_template())
        template.update(self.supported_hardware.to_template())
        return template

    def push(self, callback=None):
        """Uploads package to UpdateHub server."""
        call(callback, 'start_objects_load')
        metadata = self.to_metadata(callback)
        call(callback, 'finish_objects_load')
        objects = self.objects.to_upload()
        self.uid = push_package(metadata, objects, callback)
        return self.uid

    def __str__(self):
        return '\n'.join([
            'Product: {}'.format(self.product),
            'Version: {}'.format(self.version),
            str(self.supported_hardware),
            str(self.objects),
        ])
