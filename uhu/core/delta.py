# Copyright (C) 2021 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

ARCHIVERS = {
    # Bita format: https://github.com/oll3/bita
    'bita': {
        'signature': b'BITA1\0',
    },
}


MAX_ARCHIVER_SIGNATURE_SIZE = max(
    [len(archiver['signature']) for archiver in ARCHIVERS.values()]
)


def get_archiver_format(fn):
    """Returns the delta archiver backend for a given file.
    """
    with open(fn, 'rb') as fp:
        header = fp.read(MAX_ARCHIVER_SIGNATURE_SIZE)
    for fmt, archiver in ARCHIVERS.items():
        signature = archiver['signature']
        if signature == header[:len(signature)]:
            return fmt
    return None


def validate_delta(filename):
    if get_archiver_format(filename) is None:
        err = '"{}" doesn\'t match a known format type'
        raise ValueError(err.format(filename))
    return {}
