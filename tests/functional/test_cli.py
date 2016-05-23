# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import subprocess


def test_efu_is_a_cli_command():
    r = subprocess.call('efu')
    assert r == 0


def test_efu_can_called_as_a_module():
    r = subprocess.call(['python', '-m', 'efu'])
    assert r == 0
