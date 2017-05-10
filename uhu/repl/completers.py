# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import os

from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter

from ..core.object import Modes
from ..core.package import MODES as PKG_MODES


class ObjectFilenameCompleter(PathCompleter):

    def __init__(self):
        super().__init__(file_filter=os.path.isfile)


class ObjectModeCompleter(WordCompleter):

    def __init__(self):
        super().__init__(Modes.names())


class ObjectOptionCompleter(WordCompleter):

    def __init__(self, options):
        super().__init__(options)


class ObjectOptionValueCompleter(WordCompleter):

    def __init__(self, option):
        completions = sorted(option.choices)
        super().__init__(completions)


class ObjectUIDCompleter(WordCompleter):

    def __init__(self, package, installation_set):
        objects = enumerate(
            package.objects.get_installation_set(installation_set))
        completions = ['{}# {}'.format(index, obj.filename)
                       for index, obj in objects]
        super().__init__(sorted(completions))


class YesNoCompleter(WordCompleter):

    def __init__(self):
        completions = ['y', 'n']
        super().__init__(completions)


class PackageModeCompleter(WordCompleter):

    def __init__(self):
        super().__init__(PKG_MODES)
