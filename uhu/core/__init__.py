# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

# options must be loaded before modes. Also it must be at package
# load level so we can register all classes before anything else.
from . import options
from . import modes
from .package import Package
