# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import os

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.contrib.completers import WordCompleter

from ..core.object import Modes


class ObjectFilenameCompleter(Completer):

    DIR = 0
    LINK = 1
    FILE = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = None
        self.directory = None
        self.prefix = None
        self.filenames = None

    def get_completions(self, document, complete_event):
        try:
            self.normalize_value(document)
            self.set_base_directory()
            self.set_base_filename()
            self.set_filenames()
            return self.all_completions()
        except OSError:
            pass

    def normalize_value(self, document):
        self.value = document.text_before_cursor

    def set_base_directory(self):
        dirname = os.path.dirname(self.value)
        if dirname:
            self.directory = os.path.dirname(os.path.join('.', self.value))
        else:
            self.directory = '.'

    def set_base_filename(self):
        self.prefix = os.path.basename(self.value)

    def set_filenames(self):
        try:
            names = sorted([(fn, self._get_sort_key(fn))
                            for fn in os.listdir(self.directory)
                            if fn.startswith(self.prefix)])
        except FileNotFoundError:
            names = []
        self.filenames = sorted(names, key=lambda v: v[1])

    def all_completions(self):
        for filename, file_type in self.filenames:
            yield self.set_completion(filename, file_type)

    def set_completion(self, filename, file_type):
        completion = self._set_completion(file_type, filename)
        kwargs = self._set_completion_kwargs(file_type, filename)
        return Completion(completion, **kwargs)

    def _get_sort_key(self, fn):
        if os.path.isdir(fn):
            return self.DIR
        if os.path.islink(fn):
            return self.LINK
        return self.FILE

    def _set_completion(self, file_type, filename):
        completion = filename[len(self.prefix):]
        if file_type == self.DIR:
            completion += '/'
        return completion

    def _set_completion_kwargs(self, file_type, filename):
        kwargs = {
            'display': filename,
            'start_position': 0,
        }
        if file_type == self.DIR:
            kwargs['display'] = '{}/'.format(filename)
        elif file_type == self.LINK:
            kwargs['display'] = '{} (symbolic link)'.format(filename)
        return kwargs


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
