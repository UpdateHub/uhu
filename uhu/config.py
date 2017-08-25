# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import configparser
import os

from .utils import get_global_config_file, get_credentials


MAIN_SECTION = 'settings'
AUTH_SECTION = 'auth'


class Config:
    """This is the wrapper to manage ~/.uhu configuration file."""

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self._filename = get_global_config_file()
        self._config = configparser.ConfigParser(
            default_section=MAIN_SECTION)

    def get_credentials(self):
        env_credentials = get_credentials()
        config_credentials = self.get_credentials_from_config()
        credentials = env_credentials or config_credentials
        if not credentials:
            raise ValueError('Could not find any crendentials.')
        return credentials

    def set_credentials(self, access_id, access_secret):
        """Set server requried credentials."""
        self.set('access_id', access_id, section=AUTH_SECTION)
        self.set('access_secret', access_secret, section=AUTH_SECTION)

    def get_credentials_from_config(self):
        access = self.get('access_id', AUTH_SECTION)
        secret = self.get('access_secret', AUTH_SECTION)
        if access and secret:
            return access, secret

    def _read(self):
        if os.path.exists(self._filename):
            self._config.read(self._filename)
        open(self._filename, 'a').close()

    def set(self, key, value, section=None):
        """Adds a new entry on settings based on key and value."""
        self._read()

        if section is None:
            section = MAIN_SECTION
        elif not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, key, value)

        with open(self._filename, 'w') as fp:
            self._config.write(fp)

    def get(self, key, section=None):
        """Gets the value for the given a key."""
        self._read()
        if not section:
            section = MAIN_SECTION
        value = self._config.get(section, key, fallback=None)
        return value


config = Config()  # pylint: disable=invalid-name
