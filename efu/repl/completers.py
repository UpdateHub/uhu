# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from prompt_toolkit.contrib.completers import PathCompleter, WordCompleter

from ..core.options import MODES
from ..core.package import MODES as PKG_MODES
from ..core.package import ACTIVE_INACTIVE_MODES


class ObjectFilenameCompleter(PathCompleter):

    def __init__(self):
        super().__init__(file_filter=os.path.isfile)


class ObjectModeCompleter(WordCompleter):

    def __init__(self):
        super().__init__(sorted(MODES))


class ObjectOptionCompleter(WordCompleter):

    def __init__(self, options):
        super().__init__(sorted(options))


class ObjectOptionValueCompleter(WordCompleter):

    def __init__(self, option):
        completions = sorted(option.choices)
        super().__init__(completions)


class ObjectUIDCompleter(WordCompleter):

    def __init__(self, package, index):
        objects = enumerate(package.objects.get_set(index))
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


class ActiveInactiveCompleter(WordCompleter):

    def __init__(self):
        super().__init__(ACTIVE_INACTIVE_MODES)
