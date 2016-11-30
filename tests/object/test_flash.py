# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from efu.core.object import Object
from efu.core.package import Package
from efu.core.installation_set import InstallationSetMode
from efu.utils import validate_schema

from utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


class FlashObjectTestCase(
        EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def setUp(self):
        super().setUp()
        cwd = os.getcwd()
        os.chdir('tests/fixtures/object')
        self.addCleanup(os.chdir, cwd)

    def get_fixture(self, fn):
        with open(fn) as fp:
            return fp.read().strip()

    def test_can_create_object(self):
        obj = Object(
            __file__, mode='flash', options={'target-device': '/dev/sda'})
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'flash')
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_string_representation(self):
        expected = self.get_fixture('flash_default.txt')
        options = {'target-device': '/dev/sda'}
        obj = Object('flash_default.txt', mode='flash', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_object_template(self):
        obj = Object(
            __file__, mode='flash', options={'target-device': '/dev/sda'})
        expected = {
            'mode': 'flash',
            'filename': __file__,
            'options': {
                'install-condition': 'always',
                'target-device': '/dev/sda',
            }
        }
        observed = obj.template()
        self.assertEqual(expected, observed)

    def test_object_metadata(self):
        fn = self.create_file(b'spam')
        sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        obj = Object(fn, mode='flash', options={'target-device': '/dev/sda'})
        obj.load()
        expected = {
            'mode': 'flash',
            'filename': fn,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb',  # nopep8
            'size': 4,
            'target-device': '/dev/sda'
        }
        observed = obj.metadata()
        self.assertIsNone(validate_schema('flash-object.json', observed))
        self.assertEqual(observed, expected)

    def test_can_load_from_file(self):
        # dumping
        pkg_fn = self.create_file(b'')
        pkg = Package(InstallationSetMode.Single)
        pkg.objects.add(__file__, 'flash', {'target-device': '/dev/sda'})
        obj = pkg.objects.get(0)
        expected = obj.template(), obj.metadata()
        pkg.dump(pkg_fn)

        # loading
        pkg = Package.from_file(pkg_fn)
        obj = pkg.objects.get(0)
        observed = obj.template(), obj.metadata()
        self.assertEqual(observed, expected)

    def test_can_load_from_metadata(self):
        obj = Object(__file__, 'flash', {'target-device': '/dev/sda'})
        obj.load()
        metadata = {
            'product': None,
            'version': None,
            'objects': [[obj.metadata()]]
        }
        pkg = Package.from_metadata(metadata)
        loaded_obj = pkg.objects.get(0)
        self.assertEqual(obj.metadata(), loaded_obj.metadata())
