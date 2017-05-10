# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

from ._base import Modes


class ObjectUploadResult:
    SUCCESS = 1
    EXISTS = 2
    FAIL = 3

    OK_RESULTS = (SUCCESS, EXISTS)

    @classmethod
    def is_ok(cls, result):
        return result in cls.OK_RESULTS


class Object:

    def __new__(cls, mode_name, values):
        cls = Modes.get(mode_name)
        return cls(values)

    @classmethod
    def to_install_condition(cls, metadata):
        iid = metadata.get('install-if-different')
        if iid == 'sha256sum':
            return {'install-condition': 'content-diverges'}
        condition = {
            'install-condition': 'version-diverges',
        }
        pattern = iid.get('pattern')
        if pattern in ['linux-kernel', 'u-boot']:
            condition['install-condition-pattern-type'] = pattern
        else:
            condition['install-condition-pattern-type'] = 'regexp'
            condition['install-condition-pattern'] = pattern.get('regexp')
            condition['install-condition-seek'] = pattern.get('seek', 0)
            condition['install-condition-buffer-size'] = pattern.get('buffer-size', -1)  # nopep8
        return condition
