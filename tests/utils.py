# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import os
import shutil
import tempfile
import unittest


class UHUTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.clean)

    def clean(self):
        pass


class FileFixtureMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._files = []

    def create_file(self, content='', name=None):
        if isinstance(content, str):
            content = content.encode()
        _, fn = tempfile.mkstemp(prefix='updatehub_')
        if name is not None:
            shutil.move(fn, name)
            fn = name
        self._files.append(fn)
        with open(fn, 'bw') as fp:
            fp.write(content)
        return fn

    @staticmethod
    def remove_file(fn):
        try:
            os.remove(fn)
        except FileNotFoundError:
            pass  # already deleted

    @staticmethod
    def read_file(fn):
        with open(fn) as fp:
            return fp.read().strip()

    @staticmethod
    def sha256sum(data):
        return hashlib.sha256(data).hexdigest()

    def clean(self):
        super().clean()
        while self._files:
            self.remove_file(self._files.pop())


class EnvironmentFixtureMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vars = []

    @staticmethod
    def remove_env_var(var):
        try:
            del os.environ[var]
        except KeyError:
            pass  # already deleted

    def set_env_var(self, var, value):
        self._vars.append(var)
        os.environ[var] = str(value)

    def clean(self):
        super().clean()
        for var in self._vars:
            self.remove_env_var(var)
