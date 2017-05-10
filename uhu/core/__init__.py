# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

# options must be loaded before modes. Also it must be at package
# load level so we can register all classes before anything else.
from . import options
from . import modes
from . package import Package
