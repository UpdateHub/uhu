# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License


class InvalidMetadataError(Exception):
    pass


class InvalidPackageObjectError(Exception):
    pass


class InvalidObjectError(Exception):
    pass


class PackageObjectExistsError(Exception):
    pass


class PackageObjectDoesNotExistError(Exception):
    pass


class ObjectDoesNotExistError(Exception):
    pass
