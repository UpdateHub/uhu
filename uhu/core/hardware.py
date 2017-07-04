# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

# Keyword used to identify that all hardware identifiers are supported
ANY = 'any'

SUPPORTED_HARDWARE_ERROR = 'Cannot parse supported-hardware'


class SupportedHardwareManager:
    """Supported hardware manager."""

    # Metadata schema property name
    metadata = 'supported-hardware'

    def __init__(self):
        self._hardware = set()

    @classmethod
    def from_file(cls, dump):
        """Reads supported hardware from a template dump.

        Raises ValueError if supported hardware is invalid.
        """
        return cls._from_dict(dump)

    @classmethod
    def from_metadata(cls, metadata):
        """Reads supported hardware from a metadata.

        Raises ValueError if supported hardware is invalid.
        """
        return cls._from_dict(metadata)

    @classmethod
    def _from_dict(cls, dict_):
        manager = cls()
        hardware_list = dict_.get(cls.metadata)
        if hardware_list == ANY:
            hardware_list = []
        try:
            for hardware in hardware_list:
                manager.add(hardware)
            return manager
        except TypeError:
            raise ValueError(SUPPORTED_HARDWARE_ERROR)

    def all(self):
        """Returns all supported hardware indentifiers alphabetically."""
        return sorted(self._hardware)

    def add(self, hardware):
        """Adds a new supported hardware identifier."""
        self._hardware.add(hardware)

    def remove(self, hardware):
        """Tries to remove a supported hardware identifier from the list.

        Raises KeyError if identifier does not exist."""
        try:
            self._hardware.remove(hardware)
        except KeyError:
            err = 'Hardware "{}" does not exist or is already removed.'
            raise KeyError(err.format(hardware))

    def to_metadata(self):
        """Serializes supported hardware as template."""
        if not self:
            return {self.metadata: ANY}
        return {self.metadata: self.all()}

    def to_template(self):
        """Serializes supported hardware as template."""
        return self.to_metadata()

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return len(self._hardware)

    def __str__(self):
        hardware = ', '.join(self.all()) or ANY
        return 'Supported hardware: {}'.format(hardware)
