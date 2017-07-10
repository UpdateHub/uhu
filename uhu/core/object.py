# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from copy import deepcopy

from ._object import Modes


class Object:  # pylint: disable=too-few-public-methods

    def __new__(cls, options):
        opts = deepcopy(options)
        mode = opts.pop('mode')
        cls = Modes.get(mode)
        return cls(opts)
