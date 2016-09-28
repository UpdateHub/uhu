# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
import tempfile
import unittest


class EFUTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.clean)

    def clean(self):
        pass


class FileFixtureMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._files = []

    def create_file(self, content=None):
        if not isinstance(content, bytes):
            content = content.encode()
        _, fn = tempfile.mkstemp()
        self._files.append(fn)
        with open(fn, 'bw') as fp:
            fp.write(content)
        return fn

    def remove_file(self, fn):
        try:
            os.remove(fn)
        except FileNotFoundError:
            pass  # already deleted

    def sha256sum(self, data):
        return hashlib.sha256(data).hexdigest()

    def clean(self):
        super().clean()
        while self._files:
            self.remove_file(self._files.pop())


class EnvironmentFixtureMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vars = []

    def remove_env_var(self, var):
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
