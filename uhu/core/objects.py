# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from itertools import chain

from .object import Object
from ._options import Options

from ..utils import call, list_to_str


class ObjectsManager:

    metadata = 'objects'

    MIN_N_SETS = 1
    MAX_N_SETS = 2

    def __init__(self, n_sets=2, dump=None):
        self.n_sets = None
        self.objects = None
        if dump is None:
            self._init_empty(n_sets)
        else:
            self._init_from_dump(dump)

    def _init_empty(self, n_sets):
        self.n_sets = self._validate_n_sets(n_sets)
        self.objects = []

    def _init_from_dump(self, dump):
        sets = dump.get(self.metadata)
        if sets is None:
            raise ValueError('objects key is not present within dump')
        if not isinstance(sets, list):
            raise TypeError('objects key has an invalid value type')
        self.n_sets = self._validate_n_sets(len(sets))
        self.objects = [tuple(Object(obj) for obj in objs)
                        for objs in zip(*sets)]
        self.sort()

    def _validate_n_sets(self, n_sets):
        if n_sets < self.MIN_N_SETS or n_sets > self.MAX_N_SETS:
            error = ('It is only possible to have between '
                     '{} and {} installation sets.')
            raise ValueError(error.format(self.MIN_N_SETS, self.MAX_N_SETS))
        return n_sets

    def load(self, callback=None):
        call(callback, 'start_objects_load')
        for obj in self.all():
            obj.load(callback=callback)
        call(callback, 'finish_objects_load')

    def create(self, options):
        """Creates a new object in all installation sets."""
        normalized_options = self._normalize_create_options_values(options)
        entry = self._create_object_entry(normalized_options)
        self.objects.append(entry)
        self.sort()
        return self.objects.index(entry)

    def _normalize_create_options_values(self, options):
        """Returns a tuple of options with n_sets size."""
        normalized_options = {}
        for opt, values in options.items():
            if not isinstance(values, tuple):
                values = tuple(values for _ in range(self.n_sets))
            normalized_options[opt] = values
        return normalized_options

    def _create_object_entry(self, options):
        entry = []
        for set_index in range(self.n_sets):
            obj_options = {}
            for opt, values in options.items():
                obj_options[opt] = values[set_index]
            entry.append(Object(obj_options))
        return entry

    def get(self, obj_index, set_index):
        """Retrives an object from an given installation set."""
        try:
            return self.objects[obj_index][set_index]
        except IndexError:
            raise ValueError('Object not found')

    def update(self, obj_index, option, value, set_index=None):
        """Updates an object option value."""
        option = Options.get(option)
        if option.symmetric:
            self._update_symmetric_option(obj_index, option, value)
        else:
            self._update_asymmetric_option(obj_index, set_index, option, value)

    def _update_symmetric_option(self, obj_index, option, value):
        for obj in self.objects[obj_index]:
            obj.update(option.metadata, value)

    def _update_asymmetric_option(self, obj_index, set_index, option, value):
        if set_index is None:
            error = 'You must specify an installation set for this option'
            raise ValueError(error)
        obj = self.objects[obj_index][set_index]
        obj.update(option.metadata, value)

    def remove(self, obj_index):
        """Removes an object from all sets."""
        try:
            self.objects.pop(obj_index)
        except IndexError:
            raise ValueError('Object not found')

    def all(self):
        """Returns all objects from all sets."""
        return list(chain.from_iterable(self.objects))

    def sort(self):
        self.objects.sort(key=lambda objs: objs[0].filename)

    def is_single(self):
        """Checks if it is single mode."""
        return self.n_sets == 1

    def to_metadata(self, callback=None):
        sets = self._to_list_of_sets()
        objects = [[obj.to_metadata(callback) for obj in set_]
                   for set_ in sets]
        return {self.metadata: objects}

    def to_template(self):
        sets = self._to_list_of_sets()
        objects = [[obj.to_template() for obj in set_] for set_ in sets]
        return {self.metadata: objects}

    def to_upload(self):
        sets = self._to_list_of_sets()
        objects = [obj.to_upload() for obj in sets[0]]
        return objects

    def _to_list_of_sets(self):
        return [[objs[set_index] for objs in self.objects]
                for set_index in range(self.n_sets)]

    def __eq__(self, other):
        return self.to_metadata() == other.to_metadata()

    def __getitem__(self, set_index):
        """Returns an installation set."""
        if not isinstance(set_index, int):
            raise TypeError('Installation set index must be a integer')
        if set_index < 0 or set_index > self.n_sets:
            raise IndexError('Installation set not found')
        return [objs[set_index] for objs in self.objects]

    def __len__(self):
        return self.n_sets

    def __str__(self):
        if not self.all():
            return 'Objects: None'
        sets = self._to_list_of_sets()
        lst = [self._objects_to_str(objects) for objects in sets]
        return list_to_str('Objects', lst)

    @staticmethod
    def _objects_to_str(objects):
        """Returns a installation set string representation."""
        lst = [str(obj) for obj in objects]
        return list_to_str('Installation Set', lst)
