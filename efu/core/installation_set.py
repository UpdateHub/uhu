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

    def add(self, *args, **kwargs):
        """Adds an object instance. Returns an Object instance."""
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
            self._add_set()

    def _add_set(self):
        """Creates a new installation set."""
        if len(self) < self.mode.value:
            objects = InstallationSet()
            self._sets.append(objects)
            return objects
        err = 'It is not possible to have more than {} set(s)'
        raise ValueError(err.format(self.mode.value))

    def get_set(self, index=None):
        """Returns an installation set."""
        if index is None:
            if self.is_single():
                index = 0
            else:
                err = 'You need to specify an index in non single mode'
                raise TypeError(err)
        try:
            return self._sets[index]
        except IndexError:
            raise ValueError('Installation set not found')

    def add(self, *args, index=None, **kw):
        """Adds a new object in a given installation set."""
        objects = self.get_set(index)
        return objects.add(*args, **kw)

    def get(self, *args, index=None, **kw):
        """Retrives an object."""
        objects = self.get_set(index)
        return objects.get(*args, **kw)

    def update(self, *args, index=None, **kw):
        """Updates an object option."""
        objects = self.get_set(index)
        objects.update(*args, **kw)

    def remove(self, *args, index=None, **kw):
        """Removes an object."""
        objects = self.get_set(index)
        objects.remove(*args, **kw)

    def all(self):
        """Returns all objects from installation sets."""
        return (obj for objects in self for obj in objects)

    def is_single(self):
        """Checks if it is single mode."""
        return self.mode is InstallationSetMode.Single

    def metadata(self):
        return [objects.metadata() for objects in self]

    def template(self):
        return [objects.template() for objects in self]

    def __iter__(self):
        return iter(objects for objects in self._sets)

    def __len__(self):
        return len(self._sets)

    def __str__(self):
        s = []
        s.append('Objects:\n')
        for index, objects in enumerate(self):
            s.append('    {}# {}\n'.format(index, indent(str(objects), 4)))
        return '\n'.join(s)
