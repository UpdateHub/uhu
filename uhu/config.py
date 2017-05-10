# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import configparser
import os

from .utils import get_global_config_file


class Sections:
    MAIN = 'settings'
    AUTH = 'auth'


class Config:
    """This is the wrapper to manage ~/.uhu configuration file."""

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self._filename = get_global_config_file()
        self._config = configparser.ConfigParser(
            default_section=Sections.MAIN)

    def _read(self):
        if os.path.exists(self._filename):
            self._config.read(self._filename)
        open(self._filename, 'a').close()

    def set_initial(self, access_id, access_secret):
        """Set server requried credentials."""
        self.set('access_id', access_id, section=Sections.AUTH)
        self.set('access_secret', access_secret, section=Sections.AUTH)

    def set(self, key, value, section=None):
        """Adds a new entry on settings based on key and value."""
        self._read()

        if section is None:
            section = Sections.MAIN
        elif not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, key, value)

        with open(self._filename, 'w') as fp:
            self._config.write(fp)

    def get(self, key, section=None):
        """Gets the value for the given a key."""
        self._read()
        if not section:
            section = Sections.MAIN
        value = self._config.get(section, key, fallback=None)
        return value


config = Config()
