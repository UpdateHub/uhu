# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from efu.core.object import Object
from efu.core.package import Package
from efu.utils import validate_schema

from utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


class UBIObjectTestCase(
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
        obj = Object(__file__, mode='ubi', options={'volume': 'system'})
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'ubi')
        self.assertEqual(obj.options['volume'], 'system')

    def test_string_representation(self):
        expected = self.get_fixture('ubi_default.txt')
        options = {'volume': 'ubi-volume'}
        obj = Object('ubi_default.txt', mode='ubi', options=options)
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_object_template(self):
        obj = Object(__file__, mode='ubi', options={'volume': 'system'})
        expected = {
            'mode': 'ubi',
            'filename': __file__,
            'options': {
                'volume': 'system'
            }
        }
        observed = obj.template()
        self.assertEqual(expected, observed)

    def test_object_metadata(self):
        fn = self.create_file(b'spam')
        sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        obj = Object(fn, mode='ubi', options={'volume': 'system'})
        obj.load()
        expected = {
            'mode': 'ubi',
            'filename': fn,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb',  # nopep8
            'size': 4,
            'volume': 'system'
        }
        observed = obj.metadata()
        self.assertIsNone(validate_schema('ubi-object.json', observed))
        self.assertEqual(observed, expected)

    def test_can_load_from_file(self):
        # dumping
        pkg_fn = self.create_file(b'')
        pkg = Package()
        pkg.objects.add_list()
        pkg.objects.add(__file__, 'ubi', {'volume': 'system'})
        obj = pkg.objects.get(0)
        expected = obj.template(), obj.metadata()
        pkg.dump(pkg_fn)

        # loading
        pkg = Package.from_file(pkg_fn)
        obj = pkg.objects.get(0)
        observed = obj.template(), obj.metadata()
        self.assertEqual(observed, expected)

    def test_can_load_from_metadata(self):
        obj = Object(__file__, 'ubi', {'volume': 'system'})
        obj.load()
        metadata = {
            'product': None,
            'version': None,
            'objects': [[obj.metadata()]]
        }
        pkg = Package.from_metadata(metadata)
        loaded_obj = pkg.objects.get(0)
        self.assertEqual(obj.metadata(), loaded_obj.metadata())
