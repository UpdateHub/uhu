# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from copy import deepcopy

from ._base import Modes


class Object:

    def __new__(cls, mode_name, values):
        cls = Modes.get(mode_name)
        return cls(values)

    @classmethod
    def from_file(cls, dump):
        options = deepcopy(dump)
        mode = options.pop('mode')
        return cls(mode, options)

    @classmethod
    def from_metadata(cls, metadata):
        options = deepcopy(metadata)
        mode = options.pop('mode')
        install_condition = cls.iid_to_ic(options)
        options.update(install_condition)
        return cls(mode, options)

    @staticmethod
    def iid_to_ic(metadata):
        """Converts meadata install-if-different key to install-condition."""
        iid = metadata.pop('install-if-different', None)
        if iid is None:
            return {}
        if iid == 'sha256sum':
            return {'install-condition': 'content-diverges'}
        # pylint: disable=invalid-name
        ic = {'install-condition': 'version-diverges'}
        pattern = iid.get('pattern')
        if pattern in ['linux-kernel', 'u-boot']:
            ic['install-condition-pattern-type'] = pattern
        else:
            ic['install-condition-pattern-type'] = 'regexp'
            ic['install-condition-pattern'] = pattern.get('regexp')
            ic['install-condition-seek'] = pattern.get('seek', 0)
            ic['install-condition-buffer-size'] = pattern.get('buffer-size', -1)  # nopep8
        return ic
