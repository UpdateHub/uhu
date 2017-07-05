# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os

from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter

from ..core.object import Modes
from ..core.package import MODES as PKG_MODES


# pylint: disable=too-few-public-methods
class ObjectFilenameCompleter(PathCompleter):

    def __init__(self):
        super().__init__(file_filter=os.path.isfile)


# pylint: disable=too-few-public-methods
class ObjectModeCompleter(WordCompleter):

    def __init__(self):
        super().__init__(Modes.names())


# pylint: disable=too-few-public-methods
class ObjectOptionValueCompleter(WordCompleter):

    def __init__(self, option):
        completions = sorted(option.choices)
        super().__init__(completions)


# pylint: disable=too-few-public-methods
class ObjectUIDCompleter(WordCompleter):

    def __init__(self, package, installation_set):
        objects = enumerate(package.objects[installation_set])
        completions = ['{}# {}'.format(index, obj.filename)
                       for index, obj in objects]
        super().__init__(sorted(completions))


# pylint: disable=too-few-public-methods
class YesNoCompleter(WordCompleter):

    def __init__(self):
        completions = ['y', 'n']
        super().__init__(completions)


# pylint: disable=too-few-public-methods
class PackageModeCompleter(WordCompleter):

    def __init__(self):
        super().__init__(PKG_MODES)
