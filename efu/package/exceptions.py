# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License


class InvalidPackageFileError(Exception):
    pass


class InvalidFileError(Exception):
    pass


class PackageFileExistsError(Exception):
    pass


class PackageFileDoesNotExistError(Exception):
    pass


class ImageDoesNotExistError(Exception):
    pass
