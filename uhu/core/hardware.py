# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

# Keyword used to identify that all hardware identifiers are supported
ANY = 'any'

SUPPORTED_HARDWARE_ERROR = 'supported-hardware key has an invalid value.'


class SupportedHardwareManager:
    """Supported hardware manager."""

    # Metadata schema property name
    metadata = 'supported-hardware'

    def __init__(self, dump=None):
        if dump is None:
            self._hardware = set()
        else:
            self._hardware = self._from_dump(dump)

    def _from_dump(self, dump):
        value = dump.get(self.metadata)
        if value is None:
            raise ValueError(SUPPORTED_HARDWARE_ERROR)
        if value == ANY:
            return set()
        if isinstance(value, str):
            raise ValueError(SUPPORTED_HARDWARE_ERROR)
        try:
            return set(value)
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

    def reset(self):
        """Removes all hardware indentifiers from set."""
        self._hardware.clear()

    def to_metadata(self):
        """Serializes supported hardware as template."""
        if not self:
            return {self.metadata: ANY}
        return {self.metadata: self.all()}

    def to_template(self):
        """Serializes supported hardware as template."""
        return self.to_metadata()

    def __eq__(self, other):
        return self.to_metadata() == other.to_metadata()

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return len(self._hardware)

    def __str__(self):
        hardware = ', '.join(self.all()) or ANY
        return 'Supported hardware: {}'.format(hardware)
