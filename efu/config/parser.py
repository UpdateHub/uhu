# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..cliparser import CLIBaseSubparser
from . import config as efu_config


class ConfigParser(CLIBaseSubparser):

    def set(self, parser):
        """
        Creates and configures the config parser
        """
        self.parser = parser
        self.parser.config_parser = self.parser.subparsers.add_parser(
            'config',
            help='Configures efu utility',
        )
        self.commands = self.parser.config_parser.add_subparsers()
        self.set_init_command()
        self.set_set_command()
        self.set_get_command()

    def handler(self):
        """
        This method should handle the default behavior of config command
        (which should be the init subcommand).

        However, Python 3.4 has a bug (https://bugs.python.org/9351)
        with nested argparsers and we can't have a default behavior in
        the way it is right now.

        The temporary solution is to create explicitly the init
        command and to do not bind anything into default handler. When
        Python 3.4 gets obsolete, we can safely move the init command
        to here.
        """
        pass

    def set_set_command(self):
        """
        Creates the config set command to store or replace a given
        configuration entry.

        $ efu config set <key> <value> --section=settings
        """
        set_command = self.commands.add_parser(
            'set',
            help='creates or replace a entry on configuration'
        )
        set_command.add_argument(
            'key',
            help='the configuration entry key'
        )
        set_command.add_argument(
            'value',
            help='the value to be set'
        )
        set_command.add_argument(
            '--section', '-s',
            help='the section to write the configuration (settings by default)'
        )
        set_command.set_defaults(handler=self.set_handler)

    def set_get_command(self):
        """
        Creates the config get command to retrieve the value of a given
        configuration entry.

        $ efu config get <key> --section=settings
        """
        get_command = self.commands.add_parser(
            'get',
            help='gets a value from configuration'
        )
        get_command.add_argument('key')
        get_command.add_argument('--section')
        get_command.set_defaults(handler=self.get_handler)

    def set_init_command(self):
        """
        Creates the config init command to initalize efu settings file.

        $ efu config init
        """
        init_command = self.commands.add_parser(
            'init',
            help='sets efu required initial configuration'
        )
        init_command.set_defaults(handler=self.init_handler)

    def init_handler(self):
        efu_config.set_initial()

    def set_handler(self):
        efu_config.set(
            self.parser.args.key,
            self.parser.args.value,
            section=self.parser.args.section,
        )

    def get_handler(self):
        value = efu_config.get(
            self.parser.args.key,
            section=self.parser.args.section,
        )
        if value:
            print(value)
