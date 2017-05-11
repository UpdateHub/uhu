# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from humanize.filesize import naturalsize

from ._options import (
    AbsolutePathOption, BooleanOption, IntegerOption, StringOption)


class Chip0DevicePath(AbsolutePathOption):
    metadata = 'chip_0_device_path'
    help = 'The device path of Chip 0'
    cli = ['--chip0-device-path']
    verbose_name = 'Chip-0 device path'


class Chip1DevicePath(AbsolutePathOption):
    metadata = 'chip_1_device_path'
    help = 'The device path of Chip 1'
    cli = ['--chip1-device-path']
    verbose_name = 'Chip-1 device path'


class ChunkSizeOption(IntegerOption):
    metadata = 'chunk-size'
    default = 131072
    min = 0
    help = ('The size of the buffers (in bytes) used to read '
            'and write (default is 128KiB)')
    cli = ['--chunk-size']
    verbose_name = 'Chunk size'

    @classmethod
    def humanize(cls, value):
        return naturalsize(value, binary=True)


class CompressedOption(BooleanOption):
    metadata = 'compressed'
    volatile = True


class CountOption(IntegerOption):
    metadata = 'count'
    default = -1
    min = -1
    help = ('How many chunk-size blocks must be copied from the source file '
            'to the target. The default value of -1 means all possible bytes '
            'until the end of the file')
    cli = ['--count']
    verbose_name = 'Count'

    @classmethod
    def humanize(cls, value):
        if value == -1:
            return 'all content'
        return value


class FilenameOption(StringOption):
    metadata = 'filename'
    verbose_name = 'filename'
    min = 1


class FilesystemOption(StringOption):
    metadata = 'filesystem'
    choices = ['btrfs', 'ext2', 'ext3', 'ext4', 'vfat',
               'f2fs', 'jffs2', 'ubifs', 'xfs']
    help = 'Filesystem type that must be used to mount the target-device'
    cli = ['--filesystem', '-fs']
    verbose_name = 'filesystem'

    @classmethod
    def humanize(cls, value):
        return value


class FormatOption(BooleanOption):
    metadata = 'format?'
    default = False
    help = ('Specifies whether the target device (target-device) '
            'should be formatted or not.')
    cli = ['--format']
    verbose_name = 'Format device'


class FormatOptionsOption(StringOption):
    metadata = 'format-options'
    help = 'Options to format target-device'
    cli = ['--format-options']
    verbose_name = 'options'
    requirements = {FormatOption: True}


class MountOptionsOption(StringOption):
    metadata = 'mount-options'
    help = 'Options to mount the filesystem in target-device'
    cli = ['--mount-options']
    verbose_name = 'Mount options'


class Padding1koption(BooleanOption):
    metadata = '1k_padding'
    help = 'If 1k-padding should be added in the head'
    cli = ['--padding-1k']
    verbose_name = '1k-padding in the head'


class SearchExponentOption(IntegerOption):
    metadata = 'search_exponent'
    help = 'The search exponent'
    cli = ['--search-exponent']
    verbose_name = 'Search exponent'


class SeekOption(IntegerOption):
    metadata = 'seek'
    default = 0
    min = 0
    help = 'How many chunk-size blocks must be skipped in the target file'
    cli = ['--seek']
    verbose_name = 'seek'


class SHA256Option(StringOption):
    metadata = 'sha256sum'
    volatile = True


class SizeOption(IntegerOption):
    metadata = 'size'
    volatile = True


class SkipOption(IntegerOption):
    metadata = 'skip'
    default = 0
    min = 0
    help = 'How many chunk-size blocks must be skipped in the source file'
    cli = ['--skip']
    verbose_name = 'Skip from source'


class TargetOption(StringOption):
    metadata = 'target'
    symmetric = False
    cli = ['--target', '-t']
    help = 'The target itself'
    verbose_name = 'Target'

    @classmethod
    def humanize(cls, value):
        return value


class TargetTypeOption(StringOption):
    metadata = 'target-type'
    cli = ['--target-type', '-tt']
    help = 'The type of target'
    verbose_name = 'Target type'

    @classmethod
    def get_choices(cls, obj):
        if obj is None:
            return cls.choices
        return obj.target_types


class TargetPathOption(AbsolutePathOption):
    metadata = 'target-path'
    symmetric = False
    cli = ['--target-path', '-tp']
    help = ('Target path on which the object must be '
            'installed to (e.g. /vmlinuz). '
            'This is relative to the mount point.')
    verbose_name = 'Target path'


class TruncateOption(BooleanOption):
    metadata = 'truncate'
    default = False
    help = ('True if the file pointed to by the target-path should be open in '
            'truncate mode (erase content before writing)')
    cli = ['--truncate']
    verbose_name = 'truncate'


class UncompressedSizeOption(IntegerOption):
    metadata = 'required-uncompressed-size'
    volatile = True


class VolumeOption(StringOption):
    metadata = 'volume'
    symmetric = False
    help = 'The volume name'
    cli = ['--volume']
    verbose_name = 'Volume name'

    @classmethod
    def humanize(cls, value):
        return value


class InstallConditionOption(StringOption):
    metadata = 'install-condition'
    choices = ['always', 'content-diverges', 'version-diverges']
    default = 'always'
    help = 'When object should be installed'
    cli = ['--install-condition']
    verbose_name = 'Install condition'

    @classmethod
    def humanize(cls, value):
        if value == 'always':
            return 'always install'
        elif value == 'content-diverges':
            return 'install when CONTENT diverges'
        elif value == 'version-diverges':
            return 'install when VERSION diverges'


class InstallConditionVersionOption(StringOption):
    metadata = 'install-condition-version'
    volatile = True


class InstallConditionPatternTypeOption(StringOption):
    metadata = 'install-condition-pattern-type'
    choices = ['linux-kernel', 'u-boot', 'regexp']
    help = 'What type of pattern to use to retrive version from object'
    cli = ['--install-condition-pattern-type']
    verbose_name = 'Version pattern type'
    requirements = {InstallConditionOption: 'version-diverges'}


class InstallConditionPatternOption(StringOption):
    metadata = 'install-condition-pattern'
    help = 'Regular expression to use when retriving version from object'
    cli = ['--install-condition-pattern']
    verbose_name = 'Version pattern'
    requirements = {InstallConditionPatternTypeOption: 'regexp'}


class InstallConditionSeekOption(IntegerOption):
    metadata = 'install-condition-seek'
    default = 0
    help = 'Place to start reading object to retrive version'
    cli = ['--install-condition-seek']
    verbose_name = 'seek'
    requirements = {InstallConditionPatternTypeOption: 'regexp'}


class InstallConditionBufferSizeOption(IntegerOption):
    metadata = 'install-condition-buffer-size'
    default = -1
    help = 'How much bytes to read object to retrive version'
    cli = ['--install-condition-buffer-size']
    verbose_name = 'buffer size'
    requirements = {InstallConditionPatternTypeOption: 'regexp'}
