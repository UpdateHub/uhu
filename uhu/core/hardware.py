# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License


class HardwareManager:
    """Supported hardware package manager."""

    def __init__(self, hardwares=None):
        self._hardwares = {} if hardwares is None else hardwares

    def all(self):
        return self._hardwares

    def count(self):
        """Returns the number of supported hardwares."""
        return len(self._hardwares)

    def get(self, hardware_name):
        """Retrives a dict representing the supported hardware."""
        return self._hardwares.get(hardware_name)

    def add(self, name, revisions=None):
        revisions = revisions if revisions is not None else []
        self._hardwares[name] = {
            'name': name,
            'revisions': sorted([rev for rev in revisions])
        }

    def remove(self, hardware):
        supported_hardware = self._hardwares.pop(hardware, None)
        if supported_hardware is None:
            err = 'Hardware {} does not exist or is already removed.'
            raise ValueError(err.format(hardware))

    def add_revision(self, hardware, revision):
        supported_hardware = self._hardwares.get(hardware)
        if supported_hardware is None:
            err = 'Hardware {} does not exist'.format(hardware)
            raise ValueError(err)
        if revision not in supported_hardware['revisions']:
            supported_hardware['revisions'].append(revision)
        supported_hardware['revisions'].sort()

    def remove_revision(self, hardware, revision):
        supported_hardware = self._hardwares.get(hardware)
        if supported_hardware is None:
            err = 'Hardware {} does not exist'.format(hardware)
            raise ValueError(err)
        try:
            supported_hardware['revisions'].remove(revision)
        except ValueError:
            err = 'Revision {} for {} does not exist or is already removed'
            raise ValueError(err.format(revision, hardware))

    def template(self):
        """Serializes supported hardware as template."""
        return self._hardwares

    def metadata(self):
        """Serializes supported hardware as template."""
        metadata = []
        for hardware, conf in self._hardwares.items():
            if not conf['revisions']:
                metadata.append({
                    'hardware': hardware,
                })
            for revision in conf['revisions']:
                metadata.append({
                    'hardware': hardware,
                    'hardware-rev': revision
                })
        metadata.sort(key=lambda v: (v['hardware'], v.get('hardware')))
        return metadata

    def __str__(self):
        if self.count() == 0:
            return 'Supported hardware: all'
        s = []
        s.append('Supported hardware:')
        s.append('')
        for i, name in enumerate(sorted(self._hardwares), 1):
            revisions = ', '.join(self.get(name)['revisions'])
            revisions = revisions if revisions else 'all'
            s.append('  {}# {} [revisions: {}]'.format(i, name, revisions))
            s.append('')
        return '\n'.join(s)
