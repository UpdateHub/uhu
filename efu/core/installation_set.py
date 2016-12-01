# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from enum import Enum, unique

from .object import Object

from ..utils import indent


class InstallationSet:
    """Low level package objects manager.

    Represents a list of Object instances.
    """

    def __init__(self):
        self._objects = []

    def create(self, *args, **kwargs):
        """Creates an object instance. Returns an Object instance."""
        obj = Object(*args, **kwargs)
        self._objects.append(obj)
        return obj

    def get(self, index):
        """Retrives an object by index."""
        try:
            return self._objects[index]
        except IndexError:
            raise ValueError('Object not found')

    def update(self, index, *args, **kwargs):
        """Given an object id, sets obj.option to value."""
        obj = self.get(index)
        obj.update(*args, **kwargs)

    def remove(self, index):
        """Removes an object."""
        try:
            return self._objects.pop(index)
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

    def create(self, *args, index=None, **kw):
        """Creates a new object in a given installation set."""
        installation_set = self.get_installation_set(index)
        return installation_set.create(*args, **kw)

    def get(self, *args, index=None, **kw):
        """Retrives an object."""
        installation_set = self.get_installation_set(index)
        return installation_set.get(*args, **kw)

    def update(self, *args, index=None, **kw):
        """Updates an object option."""
        installation_set = self.get_installation_set(index)
        installation_set.update(*args, **kw)

    def remove(self, *args, index=None, **kw):
        """Removes an object."""
        installation_set = self.get_installation_set(index)
        installation_set.remove(*args, **kw)

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
        s = []
        s.append('Objects:\n')
        for index, installation_set in enumerate(self):
            s.append('    {}# {}\n'.format(
                index, indent(str(installation_set), 4)))
        return '\n'.join(s)
