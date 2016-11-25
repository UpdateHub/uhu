# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License
"""EFU REPL, an interactive prompt to work with EasyFOTA."""

import os
import sys

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter  # nopep8
from prompt_toolkit.contrib.regular_languages import compiler

from .. import get_efu_version
from ..config import config, Sections
from ..core import Package
from ..utils import get_local_config_file

from . import functions
from .helpers import prompt, set_product_prompt


COMMANDS = {
    'cleanup': functions.clean_package,
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
        'mode': functions.set_package_mode,
        'version': functions.set_package_version,
        # objects
        'add': functions.add_object,
        'edit': functions.edit_object,
        'remove': functions.remove_object,
        'add-set': functions.add_installation_set,
        'remove-set': functions.remove_installation_set,
        # transactions
        'pull': functions.pull_package,
        'push': functions.push_package,
        'status': functions.get_package_status,
    },
    'hardware': {
        'add': functions.add_hardware,
        'remove': functions.remove_hardware,
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


class EFURepl:
    """The main class for EFU REPL."""

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
        `EFURepl` will create a new one.

        :param package_fn: An EFU package filename.
        """
        self.local_config = get_local_config_file()

        if package_fn is not None:
            self.package = Package.from_file(package_fn)
        elif os.path.exists(self.local_config):
            self.package = Package.from_file(self.local_config)
        else:
            self.package = Package()

        if self.package.product:
            self.prompt = set_product_prompt(self.package.product)
        else:
            self.prompt = 'efu> '

        self.arg = None
        self.history = InMemoryHistory()

    def repl(self):
        """Starts a new interactive prompt."""
        print('EasyFOTA Utils {}'.format(get_efu_version()))
        while True:
            expression = prompt(
                self.prompt, completer=self.completer, history=self.history)
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
            print('ERROR: {}'.format(err))
        else:  # save package in every successful command
            self.package.dump(self.local_config)


def efu_interactive(package):
    """Instantiates a new EFURepl.

    Before creating a new instance, checks if server authentication is
    set. If not, prompts user for its credentials.
    """
    access = config.get('access_id', Sections.AUTH)
    secret = config.get('access_secret', Sections.AUTH)
    if not all([access, secret]):
        functions.set_authentication()
    return EFURepl(package).repl()
