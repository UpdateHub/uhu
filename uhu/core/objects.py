# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from enum import Enum, unique

from .object import Object
from ._options import Options

from ..utils import call, indent


OBJECTS_ERROR = 'Cannot parse objects'


class InstallationSet:
    """Low level package objects manager.

    Represents a list of Object instances.
    """

    def __init__(self):
        self.objects = []

    @classmethod
    def from_file(cls, dump):
        return cls._from_dump(dump, 'from_file')

    @classmethod
    def from_metadata(cls, metadata):
        return cls._from_dump(metadata, 'from_metadata')

    @classmethod
    def _from_dump(cls, dump, constructor):
        installation_set = cls()
        obj_constructor = getattr(Object, constructor)
        installation_set.objects = [obj_constructor(obj) for obj in dump]
        return installation_set

    def create(self, options):
        """Adds an object into set, returns its index."""
        self.objects.append(Object(options))
        return len(self) - 1

    def get(self, index):
        """Retrives an object by index."""
        try:
            return self.objects[index]
        except IndexError:
            raise ValueError('Object not found')

    def update(self, index, option, value):
        """Given an object id, sets obj.option to value."""
        obj = self.get(index)
        obj.update(option, value)

    def remove(self, index):
        """Removes an object."""
        try:
            self.objects.pop(index)
        except IndexError:
            raise ValueError('Object not found')

    def to_metadata(self):
        return [obj.to_metadata() for obj in self]

    def to_template(self):
        return [obj.to_template() for obj in self]

    def __iter__(self):
        return iter(self.objects)

    def __len__(self):
        return len(self.objects)

    def __str__(self):
        string = []
        string.append('Installation Set:\n')
        for index, obj in enumerate(self):
            string.append('    {}# {}\n'.format(index, indent(str(obj), 4)))
        return '\n'.join(string)


@unique
class InstallationSetMode(Enum):
    Single = 1
    ActiveInactive = 2

    @classmethod
    def from_objects(cls, objects):
        if not objects:
            raise ValueError('There are no objects in this set.')
        return InstallationSetMode(len(objects))


class ObjectsManager:
    """High level package objects manager.

    Represents a list of InstallationSet instances with methods to
    operate objects directly.
    """

    metadata = 'objects'

    def __init__(self, mode):
        self.mode = mode
        self.sets = []
        for _ in range(self.mode.value):
            self.sets.append(InstallationSet())

    @classmethod
    def from_file(cls, dump):
        return cls._from_dump(dump, 'from_file')

    @classmethod
    def from_metadata(cls, metadata):
        return cls._from_dump(metadata, 'from_metadata')

    @classmethod
    def _from_dump(cls, dump, constructor):
        objects = dump.get(cls.metadata)
        try:
            mode = InstallationSetMode.from_objects(objects)
        except ValueError:
            raise ValueError(OBJECTS_ERROR)
        manager = cls(mode)
        set_constructor = getattr(InstallationSet, constructor)
        manager.sets = [set_constructor(installation_set)
                        for installation_set in objects]
        return manager

    def load(self, callback=None):
        call(callback, 'start_objects_load')
        for obj in self.all():
            obj.load(callback=callback)
        call(callback, 'finish_objects_load')

    def create(self, options):
        """Creates a new object in all installation sets."""
        for index, installation_set in enumerate(self):
            index_options = {}
            for opt, value in options.items():
                if isinstance(value, tuple):
                    value = value[index]
                index_options[opt] = value
            obj_index = installation_set.create(index_options)
        return obj_index

    def get(self, index, installation_set):
        """Retrives an object from an given installation set."""
        installation_set = self[installation_set]
        return installation_set.get(index)

    def update(self, index, option, value, installation_set=None):
        """Updates an object option value."""
        option = Options.get(option)
        if option.symmetric:
            if installation_set is not None:
                raise ValueError(
                    'You must not pass an installation set for this option')
            # pylint: disable=redefined-argument-from-local
            for installation_set in self:
                installation_set.update(index, option.metadata, value)
        else:
            if installation_set is None:
                raise ValueError(
                    'You must specify an installation set for this option')
            installation_set = self[installation_set]
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

    def to_metadata(self):
        objects = [installation_set.to_metadata() for installation_set in self]
        return {self.metadata: objects}

    def to_template(self):
        objects = [installation_set.to_template() for installation_set in self]
        return {self.metadata: objects}

    def __getitem__(self, index):
        """Returns an installation set."""
        try:
            return self.sets[index]
        except IndexError:
            raise IndexError('Installation set not found')
        except TypeError:
            raise TypeError('Installation set index must be a integer')

    def __iter__(self):
        return iter(self.sets)

    def __len__(self):
        return len(self.sets)

    def __str__(self):
        if not self.all():
            return 'Objects: None'
        string = []
        string.append('Objects:\n')
        for index, installation_set in enumerate(self):
            string.append('    {}# {}\n'.format(
                index, indent(str(installation_set), 4)))
        return '\n'.join(string)
