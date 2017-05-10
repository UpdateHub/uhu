# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

from enum import Enum, unique

from .object import Object
from ._options import Options

from ..utils import call, indent


class InstallationSet:
    """Low level package objects manager.

    Represents a list of Object instances.
    """

    def __init__(self):
        self._objects = []

    def create(self, mode, options):
        """Adds an object into set, returns its index."""
        self._objects.append(Object(mode, options))
        return len(self) - 1

    def get(self, index):
        """Retrives an object by index."""
        try:
            return self._objects[index]
        except IndexError:
            raise ValueError('Object not found')

    def update(self, index, option, value):
        """Given an object id, sets obj.option to value."""
        obj = self.get(index)
        obj.update(option, value)

    def remove(self, index):
        """Removes an object."""
        try:
            self._objects.pop(index)
        except IndexError:
            raise ValueError('Object not found')

    def metadata(self):
        return [obj.metadata() for obj in self]

    def template(self):
        return [obj.template() for obj in self]

    def __iter__(self):
        return iter(obj for obj in self._objects)

    def __len__(self):
        return len(self._objects)

    def __str__(self):
        s = []
        s.append('Installation Set:\n')
        for index, obj in enumerate(self):
            s.append('    {}# {}\n'.format(index, indent(str(obj), 4)))
        return '\n'.join(s)


@unique
class InstallationSetMode(Enum):
    Single = 1
    ActiveInactive = 2

    @classmethod
    def from_objects(cls, objects):
        if not objects:
            raise ValueError('There are no objects in this set.')
        return InstallationSetMode(len(objects))


class InstallationSetManager:
    """High level package objects manager.

    Represents a list of InstallationSet instances with methods to
    operate objects directly.
    """

    def __init__(self, mode):
        self.mode = mode
        self._sets = []
        for _ in range(self.mode.value):
            self._sets.append(InstallationSet())

    def get_installation_set(self, index):
        """Returns an installation set."""
        try:
            return self._sets[index]
        except IndexError:
            raise ValueError('Installation set not found')

    def load(self, callback=None):
        call(callback, 'start_objects_load')
        for obj in self.all():
            obj.load(callback=callback)
        call(callback, 'finish_objects_load')

    def create(self, mode, options):
        """Creates a new object in a given installation set."""
        for index, installation_set in enumerate(self):
            index_options = {}
            for opt, value in options.items():
                if isinstance(value, tuple):
                    value = value[index]
                index_options[opt] = value
            obj_index = installation_set.create(mode, index_options)
        return obj_index

    def get(self, index, installation_set):
        """Retrives an object from an given installation set."""
        installation_set = self.get_installation_set(installation_set)
        return installation_set.get(index)

    def update(self, index, option, value, installation_set=None):
        """Updates an object option value."""
        option = Options.get(option)
        if option.symmetric:
            if installation_set is not None:
                raise ValueError(
                    'You must not pass an installation set for this option')
            for installation_set in self:
                installation_set.update(index, option.metadata, value)
        else:
            if installation_set is None:
                raise ValueError(
                    'You must specify an installation set for this option')
            installation_set = self.get_installation_set(installation_set)
            installation_set.update(index, option.metadata, value)

    def remove(self, index):
        """Removes an object from all installation sets."""
        for installation_set in self:
            installation_set.remove(index)

    def all(self):
        """Returns all installation_set from installation sets."""
        return [obj for installation_set in self for obj in installation_set]

    def is_single(self):
        """Checks if it is single mode."""
        return self.mode is InstallationSetMode.Single

    def metadata(self):
        return [installation_set.metadata() for installation_set in self]

    def template(self):
        return [installation_set.template() for installation_set in self]

    def __iter__(self):
        return iter(installation_set for installation_set in self._sets)

    def __len__(self):
        return len(self._sets)

    def __str__(self):
        if len(self.all()) == 0:
            return 'Objects: None'
        s = []
        s.append('Objects:\n')
        for index, installation_set in enumerate(self):
            s.append('    {}# {}\n'.format(
                index, indent(str(installation_set), 4)))
        return '\n'.join(s)
