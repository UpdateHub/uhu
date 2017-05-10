# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License


class UploadError(Exception):
    pass


class DownloadError(Exception):
    pass


class CommitDoesNotExist(Exception):
    pass
