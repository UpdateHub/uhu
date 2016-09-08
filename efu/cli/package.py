# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from ..core.parser import (
    export_command, cleanup_command, add_command, remove_command, show_command)

from .pull import pull_command
from .push import push_command, status_command


@click.group(name='package')
def package_cli():
    ''' Package related commands '''
    pass


# Package commands
package_cli.add_command(show_command)
package_cli.add_command(export_command)
package_cli.add_command(cleanup_command)

# Image commands
package_cli.add_command(add_command)
package_cli.add_command(remove_command)

# Transaction commands
package_cli.add_command(pull_command)
package_cli.add_command(push_command)
package_cli.add_command(status_command)
