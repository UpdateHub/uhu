# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License


class InvalidPackageFileError(Exception):
    pass


class InvalidFileError(Exception):
    pass


class StartPushError(Exception):
    pass


class FileUploadError(Exception):
    pass


class FinishPushError(Exception):
    pass
