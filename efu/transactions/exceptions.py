# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License


class StartPushError(Exception):
    pass


class UploadError(Exception):
    pass


class DownloadError(Exception):
    pass


class FinishPushError(Exception):
    pass


class CommitDoesNotExist(Exception):
    pass
