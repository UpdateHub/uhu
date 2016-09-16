# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click


MODES = ('raw', 'copy', 'tarball')


class ObjectOptions:
    '''
    modes object:
    {
      'mode': {
        'options': {
          'option': {
            'default': str,
            'metadata': str,
            'requirements': [option],
            'callback': lambda: None
          }
        }
      }
    }
    '''

    modes = {}
    click_options = []

    def __init__(self, filename, mode, options):
        self.filename = filename
        self.mode = mode
        self.mode_options = self.modes[self.mode]['options']
        self.mode_requirements = set(self.modes[self.mode]['required'])
        self.options = {}

        for option, value in options.items():
            if value is not None:
                self.options[option] = value

    def inject_default_values(self):
        for option in self.mode_options:
            if option not in self.options:
                default = self.mode_options[option].get('default')
                if default is not None:
                    self.options[option] = default

    def validate_mode_requirements(self):
        options = self.mode_requirements - set(self.options)
        if options:
            err = 'Mode requirements not satisfied: {}'
            raise ValueError(err.format(', '.join(options)))

    def validate_options_requirements(self):
        options_set = set(self.options)
        for option, conf in self.mode_options.items():
            if option in self.options:
                if not set(conf['requirements']).issubset(options_set):
                    raise ValueError('Option requirements not satisfied')

    def validate_options_callback(self):
        for option, conf in self.mode_options.items():
            if option in self.options:
                callback = conf.get('callback')
                if callback is not None:
                    callback(self.options)

    def as_metadata(self):
        self.inject_default_values()
        self.validate_mode_requirements()
        self.validate_options_requirements()
        self.validate_options_callback()
        metadata = {
            'filename': self.filename,
            'mode': self.mode
        }
        for option, value in self.options.items():
            key = self.mode_options[option]['metadata']
            metadata[key] = value
        return metadata

    @classmethod
    def add(
            cls, option, modes, required_in=None,
            metadata=None, default=None, requires=None,
            callback=None):
        name = option.name
        cls.click_options.append(option)
        for mode in modes:
            cls.modes[mode] = cls.modes.get(
                mode, {'options': {}, 'required': []})
            cls.modes[mode]['options'][name] = {
                'default': default,
                'metadata': metadata if metadata else name,
                'requirements': requires if requires else [],
                'callback': callback,
            }
        if required_in is not None:
            for mode in required_in:
                cls.modes[mode]['required'].append(name)


# Chunk size
ObjectOptions.add(
    modes=('raw',),
    option=click.Option(
        ['--chunk-size'],
        type=click.IntRange(0),
        help=('The size of the buffers (in bytes) used to '
              'read and write (default is 128KiB)')),
    metadata='chunk-size',
    default=(128 * 1024),
)

# Count
ObjectOptions.add(
    modes=('raw',),
    option=click.Option(
        ['--count'],
        type=click.IntRange(-1),
        help=('How many chunk-size blocks must be copied from '
              'the source file to the target. The default value of -1 '
              'means all possible bytes until the end of the file')),
    default=-1
)

# Filesystem
ObjectOptions.add(
    modes=('copy', 'tarball'),
    required_in=('copy', 'tarball'),
    option=click.Option(
        ['--filesystem', '-fs'],
        help='Filesystem type that must be used to mount the target-device')
)

# Format
ObjectOptions.add(
    modes=('copy', 'tarball'),
    option=click.Option(
        ['--format/--no-format'],
        help=('Specifies whether the target device '
              '(target-device) should be formatted or not.'),
        default=None),
    metadata='format?',
    default=False
)


def format_options_callback(options):
    if not options.get('format'):
        raise ValueError('--format-options requires --format to be true.')


# Format options
ObjectOptions.add(
    modes=('copy', 'tarball'),
    option=click.Option(
        ['--format-options'],
        help='Options to format target-device'),
    metadata='format-options',
    requires=['format'],
    callback=format_options_callback,
)

# Mount options
ObjectOptions.add(
    modes=('copy', 'tarball'),
    option=click.Option(
        ['--mount-options'],
        help='Options to mount the filesystem in target-device'),
    metadata='mount-options',
)

# Seek
ObjectOptions.add(
    modes=('raw',),
    option=click.Option(
        ['--seek'],
        type=click.IntRange(0),
        help='How many chunk-size blocks must be skipped in the target file',
    ),
    default=0
)

# Skip
ObjectOptions.add(
    modes=('raw',),
    option=click.Option(
        ['--skip'],
        type=click.IntRange(0),
        help='How many chunk-size blocks must be skipped in the source file'),
    default=0
)

# Target device
ObjectOptions.add(
    modes=MODES,
    required_in=MODES,
    option=click.Option(
        ['--target-device', '-td'],
        type=click.Path(),
        help='Target device for the object (e.g. /dev/sda1)'),
    metadata='target-device'
)

# Target path
ObjectOptions.add(
    modes=('copy', 'tarball'),
    required_in=('copy', 'tarball'),
    option=click.Option(
        ['--target-path', '-tp'],
        type=click.Path(),
        help=('Target path on which the object must be installed to (e.g. '
              '/vmlinuz). This is relative to the mount point. Field present '
              'when mode equals to copy or tarball')),
    metadata='target-path'
)

ObjectOptions.add(
    modes=('raw',),
    option=click.Option(
        ['--truncate/--no-truncate'],
        help=('True if the file pointed to by the target_path should be open '
              'in truncate mode (erase content before writing)'),
        default=None),
    default=False
)
