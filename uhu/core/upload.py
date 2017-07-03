# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from enum import Enum


class ObjectUploadResult(Enum):
    SUCCESS = 1
    EXISTS = 2
    FAIL = 3

    @classmethod
    def is_ok(cls, result):
        return result in (cls.SUCCESS, cls.EXISTS)
