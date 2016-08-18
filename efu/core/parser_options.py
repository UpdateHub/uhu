# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from .parser_utils import (
    LazyPromptOption, ImageOption,
    InstallMode, InstallModeChoiceType
)


FILENAME = click.Argument(
    ['filename'],
    type=click.Path(exists=True)
)

CHUNK_SIZE = ImageOption(
    ['--chunk-size'],
    type=click.IntRange(0),
    help=('The size of the buffers (in bytes) used to '
          'read and write (default is 128KiB)'),
    default_lazy=(128 * 1024)
)

COUNT = ImageOption(
    ['--count'],
    type=click.IntRange(-1),
    help=('How many chunk-size blocks must be copied from '
          'the source file to the target. The default value of -1 means all '
          'possible bytes until the end of the file'),
    default_lazy=-1
)

FILESYSTEM = ImageOption(
    ['--filesystem', '-fs'],
    help='Filesystem type that must be used to mount the target-device'
)

FORMAT = ImageOption(
    ['--format/--no-format'],
    help=('Specifies whether the target device '
          '(target-device) should be formatted or not.'),
    default_lazy=False
)


def format_options_lazy_callback(params):
    if params.get('format'):
        return (True, None)
    return (False, '--format-options requires --format to be true.')


FORMAT_OPTIONS = ImageOption(
    ['--format-options'],
    help='Options to format target-device',
    dependencies=[FORMAT],
    callback_lazy=format_options_lazy_callback
)

MOUNT_OPTIONS = ImageOption(
    ['--mount-options'],
    help='Options to mount the filesystem in target-device',
)

SEEK = ImageOption(
    ['--seek'],
    type=click.IntRange(0),
    help='How many chunk-size blocks must be skipped in the target file',
    default_lazy=0
)

SKIP = ImageOption(
    ['--skip'],
    type=click.IntRange(0),
    help='How many chunk-size blocks must be skipped in the source file',
    default_lazy=0
)

TARGET_DEVICE = ImageOption(
    ['--target-device', '-td'],
    type=click.Path(),
    help='Target device for the image (e.g. /dev/sda1)'
)

TARGET_PATH = ImageOption(
    ['--target-path', '-tp'],
    type=click.Path(),
    help=('Target path on which the image must be installed to (e.g. '
          '/vmlinuz). This is relative to the mount point. Field present when '
          'install-mode equals to copy or tarball')
)

TRUNCATE = ImageOption(
    ['--truncate/--no-truncate'],
    help=('True if the file pointed to by the target_path should be open in '
          'truncate mode (erase content before writing)'),
    default_lazy=False
)


# INSTALL MODE DEFINITIONS
MODES = {
    # COPY
    'copy': InstallMode(
        name='copy',
        required=[TARGET_DEVICE, TARGET_PATH, FILESYSTEM],
        optional=[MOUNT_OPTIONS, FORMAT, FORMAT_OPTIONS]
    ),

    # RAW
    'raw': InstallMode(
        name='raw',
        required=[TARGET_DEVICE],
        optional=[CHUNK_SIZE, COUNT, SEEK, SKIP, TRUNCATE]
    ),

    # TARBALL
    'tarball': InstallMode(
        name='tarball',
        required=[TARGET_DEVICE, TARGET_PATH, FILESYSTEM],
        optional=[MOUNT_OPTIONS, FORMAT, FORMAT_OPTIONS]
    )
}


# INSTALL MODE PARAM
def install_mode_callback(ctx, param, value):  # pylint: disable=W0613
    ctx.install_mode = value
    return value


INSTALL_MODE = LazyPromptOption(
    ['--install-mode', '-m'],
    is_eager=True,
    type=InstallModeChoiceType(MODES),
    help='How the image will be installed',
    callback=install_mode_callback
)


# Helper to avoid 'from .mode_options import *'
ALL_PARAMS = [
    FILENAME,
    INSTALL_MODE,
    CHUNK_SIZE,
    COUNT,
    FILESYSTEM,
    FORMAT,
    FORMAT_OPTIONS,
    MOUNT_OPTIONS,
    SEEK,
    SKIP,
    TARGET_DEVICE,
    TARGET_PATH,
    TRUNCATE,
]
