# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License
"""EFU REPL Package.

Here, we set some keybindings and brings to namespace
`efu_interactive` function which starts the interactive prompt.
"""

import sys
from functools import partial

from prompt_toolkit import prompt
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


manager = KeyBindingManager.for_prompt()


@manager.registry.add_binding(Keys.ControlD)
def ctrl_d(event):
    """Ctrl D quits appliaction returning 0 to sys."""
    event.cli.run_in_terminal(sys.exit(0))


@manager.registry.add_binding(Keys.ControlC)
def ctrl_c(event):
    """Ctrl C quits appliaction returning 1 to sys."""
    event.cli.run_in_terminal(sys.exit(1))


prompt = partial(prompt, key_bindings_registry=manager.registry)


from .repl import efu_interactive  # nopep8
