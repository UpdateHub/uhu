# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import json
from collections import OrderedDict


def dump_package(package, fn):
    """Dumps a package into a file."""
    with open(fn, 'w') as fp:
        json.dump(package, fp, indent=4, sort_keys=True)
        fp.write('\n')


def load_package(fn):
    """Loads a package from package dump file."""
    from .package import Package
    with open(fn) as fp:
        dump = json.load(fp, object_pairs_hook=OrderedDict)
    return Package(dump=dump)
