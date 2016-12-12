# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import tempfile
import unittest

from efu.core.package import Package
from efu.core.installation_set import InstallationSetMode


class PackageHardwareManagerIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        self.pkg = Package(InstallationSetMode.ActiveInactive)
        self.metadata = {
            'product': None,
            'version': None,
            'objects': [[], []],
            'supported-hardware': [
                {
                    'hardware': 'PowerX',
                    'hardware-rev': '1',
                },
                {
                    'hardware': 'PowerX',
                    'hardware-rev': '2',
                },
                {
                    'hardware': 'PowerY',
                },
            ]
        }
        self.template = {
            'product': None,
            'version': None,
            'objects': [[], []],
            'supported-hardware': {
                'PowerX': {
                    'name': 'PowerX',
                    'revisions': ['1', '2'],
                },
                'PowerY': {
                    'name': 'PowerY',
                    'revisions': [],
                },
            }
        }

    def test_can_add_hardwares(self):
        self.assertEqual(self.pkg.hardwares.count(), 0)
        self.pkg.hardwares.add('PowerX', revisions=['1', '2'])
        self.assertEqual(self.pkg.hardwares.count(), 1)

    def test_can_remove_hardwares(self):
        self.pkg.hardwares.add('PowerX', revisions=['1', '2'])
        self.assertEqual(self.pkg.hardwares.count(), 1)
        self.pkg.hardwares.remove('PowerX')
        self.assertEqual(self.pkg.hardwares.count(), 0)

    def test_can_add_revision(self):
        self.pkg.hardwares.add('PowerX')
        hardware = self.pkg.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 0)
        self.pkg.hardwares.add_revision('PowerX', 'rev1')
        self.assertEqual(len(hardware['revisions']), 1)

    def test_can_remove_revision(self):
        self.pkg.hardwares.add('PowerX', revisions=['rev1'])
        hardware = self.pkg.hardwares.get('PowerX')
        self.assertEqual(len(hardware['revisions']), 1)
        self.pkg.hardwares.remove_revision('PowerX', 'rev1')
        self.assertEqual(len(hardware['revisions']), 0)

    def test_can_serialize_as_template(self):
        self.pkg.hardwares.add('PowerX', revisions=['1', '2'])
        self.pkg.hardwares.add('PowerY')
        observed = self.pkg.template()
        self.assertEqual(observed, self.template)

    def test_can_serialize_as_metadata(self):
        self.pkg.hardwares.add('PowerX', revisions=['1', '2'])
        self.pkg.hardwares.add('PowerY')
        observed = self.pkg.metadata()
        self.assertEqual(observed, self.metadata)

    def test_can_load_from_file(self):
        pkg_fn = tempfile.NamedTemporaryFile()
        with open(pkg_fn.name, 'w') as fp:
            json.dump(self.template, fp)
        pkg = Package.from_file(pkg_fn.name)
        self.assertEqual(pkg.template(), self.template)

    def test_can_load_from_metadata(self):
        pkg = Package.from_metadata(self.metadata)
        self.assertEqual(pkg.metadata(), self.metadata)
