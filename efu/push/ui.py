# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import sys

import click
from progress.bar import Bar


GREEN = '\033[92m'
RED = '\033[91m'
END = '\033[0m'

SUCCESS_MSG = '{}SUCCESS{}'.format(GREEN, END)
FAIL_MSG = '{}FAIL{}'.format(RED, END)


class UploadProgressBar(Bar):
    file = sys.stdout
    file.isatty = lambda: True

    def finish_with_msg(self, msg):
        self.clearln()
        file = self.message
        click.echo('{} {}'.format(file, msg), nl=False)
        self.finish()
