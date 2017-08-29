# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0
"""UpdateHub REPL, an interactive prompt to work with firmware updates."""

import os
import sys

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter  # nopep8
from prompt_toolkit.contrib.regular_languages import compiler

from .. import get_version
from ..config import config
from ..core.package import Package
from ..core.utils import dump_package, load_package
from ..utils import get_local_config_file

from . import functions
from .exceptions import CancelPromptException
from .helpers import prompt, set_product_prompt


COMMANDS = {
    'auth': lambda _: functions.set_authentication(),
    'quit': lambda _: sys.exit(0),
    'show': functions.show_package,
    'save': functions.save_package,
}

GROUPS = {
    'product': {
        'use': functions.set_product_uid,
    },
    'package': {
        # package
        'version': functions.set_package_version,
        # objects
        'add': functions.add_object,
        'edit': functions.edit_object,
        'remove': functions.remove_object,
        # transactions
        'push': functions.push_package,
        'status': functions.package_status,
    },
    'hardware': {
        'add': functions.add_hardware,
        'remove': functions.remove_hardware,
        'reset': functions.reset_hardware,
    }
}


GRAMMAR = compiler.compile(r'''
(\s* (?P<group>product) \s+ (?P<product>[a-z]+) \s+ (?P<arg>.+?) \s*) |
(\s* (?P<group>product) \s+ (?P<product>[a-z]+) \s*) |

(\s* (?P<group>hardware) \s+ (?P<hardware>[a-z]+) \s+ (?P<arg>.+?) \s*) |
(\s* (?P<group>hardware) \s+ (?P<hardware>[a-z]+) \s*) |

(\s* (?P<group>package) \s+ (?P<package>[a-z-]+) \s+ (?P<arg>.+?) \s*) |
(\s* (?P<group>package) \s+ (?P<package>[a-z-]+) \s*) |

(\s* (?P<command>[a-z]+) \s*) |
(\s* (?P<command>[a-z]+) \s+ (?P<arg>.+?) \s*) |
''')


class UHURepl:
    """The main class for UpdateHub REPL."""

    completer = GrammarCompleter(GRAMMAR, {
        'command': WordCompleter(COMMANDS),
        'group': WordCompleter(GROUPS),
        'hardware': WordCompleter(GROUPS['hardware']),
        'product': WordCompleter(GROUPS['product']),
        'package': WordCompleter(GROUPS['package'])
    })

    def __init__(self, package_fn=None):
        """Creates a new interactive prompt.

        The interactive prompt will work using an exisiting
        configuration file (if it exists).

        It is also able to load an existing configuration file placed
        in a non standard place if REPL is created using the
        `package_fn`.

        Finally, if there is no configuration file present in the
        working directory, neighter a package file is explicty passed,
        `UHURepl` will create a new one.

        :param package_fn: An UHU package filename.
        """
        self.local_config = get_local_config_file()

        if package_fn is not None:
            self.package = self.load_package(package_fn)
        elif os.path.exists(self.local_config):
            self.package = self.load_package(self.local_config)
        else:
            self.package = Package()

        if self.package.product:
            self.prompt = set_product_prompt(self.package.product)
        else:
            self.prompt = 'uhu> '

        self.arg = None
        self.history = InMemoryHistory()

    @staticmethod
    def load_package(fn):
        try:
            return load_package(fn)
        except ValueError as err:
            print('Error: Invalid configuration file: {}'.format(err))
            sys.exit(1)

    def repl(self):
        """Starts a new interactive prompt."""
        print('UpdateHub Utils {}'.format(get_version()))
        while True:
            try:
                expression = prompt(
                    self.prompt,
                    completer=self.completer,
                    history=self.history
                )
            except CancelPromptException:
                sys.exit(1)  # User has typed Ctrl C
            try:
                command = self.get_command(expression)
            except TypeError:  # Invalid expression
                print('ERROR: Invalid command')
                continue
            except ValueError:  # Empty prompt
                continue
            else:
                self.run_command(command)

    def get_command(self, expression):
        """Given an expression, returns a valid command.

        :param expression: The full expression typed by user on
                           prompt.
        """
        expression = GRAMMAR.match(expression)

        if expression is None:
            raise TypeError

        vars_ = expression.variables()
        cmd, cmd_group = vars_.get('command'), vars_.get('group')
        self.arg = vars_.get('arg')

        if cmd is not None:
            command = COMMANDS.get(cmd)
        elif cmd_group is not None:
            group, cmd = GROUPS.get(cmd_group), vars_.get(cmd_group)
            command = group.get(cmd)
        else:
            raise ValueError('Invalid command')
        return command

    def run_command(self, command):
        """Executes an given command.

        If command runs successfully, persists the configuration state
        into a file. Otherwise, shows the error message to user.
        """
        if command is None:
            print('Invalid command')
            return
        try:
            command(self)
        except Exception as err:  # pylint: disable=broad-except
            print('\033[91mError:\033[0m {}'.format(err))
        else:  # save package in every successful command
            dump_package(self.package.to_template(), self.local_config)


def repl(package):
    """Instantiates a new UHURepl.

    Before creating a new instance, checks if server authentication is
    set. If not, prompts user for its credentials.
    """
    try:
        config.get_credentials()
    except ValueError:
        functions.set_authentication()
    try:
        config.get_private_key_path()
    except ValueError:
        functions.set_private_key()
    return UHURepl(package).repl()
