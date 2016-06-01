# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import configparser
import os


class Sections:
    main = 'settings'
    auth = 'auth'


class Config(object):
    """ This is the wrapper over ~/.efu configuration file. """

    CONFIG_FILENAME = '~/.efu'

    def __init__(self):
        self.file = self._get_config_filename()
        self.config = configparser.ConfigParser(
            default_section=Sections.main
        )
        # sets ~/.efu file if it doesn't exist
        if not os.path.exists(self.file):
            self.write()
        self.read()

    def _get_config_filename(self):
        return os.path.expanduser(self.CONFIG_FILENAME)

    def write(self):
        with open(self.file, 'w') as fp:
            self.config.write(fp)

    def read(self):
        self.config.read(self.file)

    def set_initial(self):
        """
        This set the initial required values (credentials) to run
        other efu commands.
        """
        access_key_id = input('EasyFOTA Access Key ID: ')
        access_secret_key = input('EasyFota Systems Secret Access Key: ')
        self.config[Sections.auth] = {
            'access_id': access_key_id,
            'access_secret': access_secret_key,
        }
        self.write()

    def set(self, key, value, section=Sections.main):
        """ Adds a new entry on settings based on key and value """
        if not self.config.has_section(section):
            self.config[section] = {}
        self.config.set(section, key, value)
        self.write()

    def get(self, key, section=None):
        """ Gets the value for the given a key """
        if not section:
            section = Sections.main
        value = self.config.get(section, key, fallback=None)
        if value is not None:
            print(value)
            return value


config = Config()
