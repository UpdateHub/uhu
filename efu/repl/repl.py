# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter  # nopep8
from prompt_toolkit.contrib.regular_languages import compiler

from .. import __version__
from ..core import Package

from . import functions


commands = {
    'cleanup': functions.clean_package,
    'show': functions.show_package,
    'save': functions.save_package,
}

groups = {
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


grammar = compiler.compile(r'''
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

    completer = GrammarCompleter(grammar, {
        'command': WordCompleter(commands),
        'group': WordCompleter(groups),
        'hardware': WordCompleter(groups['hardware']),
        'product': WordCompleter(groups['product']),
        'package': WordCompleter(groups['package'])
    })

    def __init__(self, package_fn=None):
        if package_fn is not None:
            self.package = Package.from_file(package_fn)
        else:
            self.package = Package()
        self.prompt = 'efu> '
        self.arg = None
        self.history = InMemoryHistory()

    def repl(self):
        print('EasyFOTA Utils {}'.format(__version__))
        while True:
            input_ = prompt(
                self.prompt, completer=self.completer, history=self.history)
            expression = grammar.match(input_)
            if expression is None:
                print('ERROR: Invalid command')
                continue
            vars_ = expression.variables()
            cmd = vars_.get('command')
            cmd_group = vars_.get('group')
            self.arg = vars_.get('arg')
            if cmd is not None:
                f = commands.get(cmd)
            elif cmd_group is not None:
                group = groups.get(cmd_group)
                cmd = vars_.get(cmd_group)
                f = group.get(cmd)
            else:
                continue
            if f is not None:
                try:
                    f(self)
                except Exception as err:  # pylint: disable=broad-except
                    print('ERROR: {}'.format(err))
            else:
                print('ERROR: Invalid command')


def efu_interactive(package):
    return EFURepl(package).repl()
