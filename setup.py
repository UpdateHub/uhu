# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from setuptools import find_packages, setup

from uhu import get_version

setup(
    version=get_version(),
    packages=find_packages(exclude=['tests*']),
)
