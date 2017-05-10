# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import subprocess

import pkg_resources


def get_version():
    """Retrives uhu package version.

    First, it tries to parse a git describe command result. If not
    successful, uses setuptools pkg_resources. If the last fails,
    returns Unknown version.
    """
    try:
        output = subprocess.check_output(
            ['git', 'describe', '--always'], stderr=subprocess.PIPE)
        version = output.decode().strip()
    except (subprocess.CalledProcessError, OSError):
        try:
            distribution = pkg_resources.get_distribution('updatehub-utils')
            return distribution.version  # pylint: disable=no-member
        except pkg_resources.DistributionNotFound:
            # Without space to be friendly with setup.py
            return 'UnknownVersion'
    if '-' in version:
        return '{}.dev{}+{}'.format(*version.split('-'))
    return version
