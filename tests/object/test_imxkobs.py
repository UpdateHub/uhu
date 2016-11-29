# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os

from efu.core.object import Object
from efu.core.package import Package
from efu.utils import validate_schema

from utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


class ImxkobsObjectTestCase(
        EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def setUp(self):
        super().setUp()
        cwd = os.getcwd()
        os.chdir('tests/fixtures/object')
        self.addCleanup(os.chdir, cwd)

    def get_fixture(self, fn):
        with open(fn) as fp:
            return fp.read().strip()

    def test_can_create_minimal_object(self):
        obj = Object(__file__, mode='imxkobs', options={})
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'imxkobs')
        self.assertIsNone(obj.options.get('1k_padding'))
        self.assertIsNone(obj.options.get('search_exponent'))
        self.assertIsNone(obj.options.get('chip_0_device_path'))
        self.assertIsNone(obj.options.get('chip_1_device_path'))

    def test_can_create_full_object(self):
        obj = Object(__file__, mode='imxkobs', options={
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        })
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'imxkobs')
        self.assertEqual(obj.options['1k_padding'], True)
        self.assertEqual(obj.options['search_exponent'], 1)
        self.assertEqual(obj.options['chip_0_device_path'], '/dev/mtd0')
        self.assertEqual(obj.options['chip_1_device_path'], '/dev/mtd1')

    def test_default_string_representation(self):
        expected = self.get_fixture('imxkobs_default.txt')
        obj = Object('imxkobs_default.txt', mode='imxkobs', options={})
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_full_string_representation(self):
        expected = self.get_fixture('imxkobs_full.txt')
        obj = Object('imxkobs_full.txt', mode='imxkobs', options={
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        })
        observed = str(obj)
        self.assertEqual(observed, expected)

    def test_minimal_object_template(self):
        obj = Object(__file__, mode='imxkobs', options={})
        expected = {
            'mode': 'imxkobs',
            'filename': __file__,
            'options': {'install-condition': 'always'}
        }
        observed = obj.template()
        self.assertEqual(expected, observed)

    def test_full_object_template(self):
        obj = Object(__file__, mode='imxkobs', options={
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        })
        expected = {
            'mode': 'imxkobs',
            'filename': __file__,
            'options': {
                'install-condition': 'always',
                "1k_padding": True,
                "search_exponent": 1,
                "chip_0_device_path": "/dev/mtd0",
                "chip_1_device_path": "/dev/mtd1",
            }
        }
        observed = obj.template()
        self.assertEqual(expected, observed)

    def test_minimal_object_metadata(self):
        fn = self.create_file(b'spam')
        sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        obj = Object(fn, mode='imxkobs', options={})
        obj.load()
        expected = {
            'mode': 'imxkobs',
            'filename': fn,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb',  # nopep8
            'size': 4,
        }
        observed = obj.metadata()
        self.assertIsNone(validate_schema('imxkobs-object.json', observed))
        self.assertEqual(observed, expected)

    def test_full_object_metadata(self):
        fn = self.create_file(b'spam')
        sha256sum = '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb'  # nopep8
        obj = Object(fn, mode='imxkobs', options={
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        })
        obj.load()
        expected = {
            'mode': 'imxkobs',
            'filename': fn,
            'sha256sum': '4e388ab32b10dc8dbc7e28144f552830adc74787c1e2c0824032078a79f227fb',  # nopep8
            'size': 4,
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        }
        observed = obj.metadata()
        self.assertIsNone(validate_schema('imxkobs-object.json', observed))
        self.assertEqual(observed, expected)

    def test_can_load_from_file(self):
        # dumping
        pkg_fn = self.create_file(b'')
        pkg = Package()
        pkg.objects.add_list()
        pkg.objects.add(__file__, 'imxkobs', {})
        pkg.objects.add(__file__, 'imxkobs', options={
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        })
        expected = [(obj.template(), obj.metadata())
                    for obj in pkg.objects.all()]
        pkg.dump(pkg_fn)

        # loading
        pkg = Package.from_file(pkg_fn)
        observed = [(obj.template(), obj.metadata())
                    for obj in pkg.objects.all()]
        self.assertEqual(observed, expected)

    def test_can_load_from_metadata(self):
        option_set = [{}, {
            "1k_padding": True,
            "search_exponent": 1,
            "chip_0_device_path": "/dev/mtd0",
            "chip_1_device_path": "/dev/mtd1",
        }]
        objs = [Object(__file__, 'imxkobs', opt) for opt in option_set]
        for obj in objs:
            obj.load()

        metadata = {
            'product': None,
            'version': None,
            'objects': [[obj.metadata() for obj in objs]]
        }
        pkg = Package.from_metadata(metadata)
        expected = [obj.metadata() for obj in objs]
        observed = [obj.metadata() for obj in pkg.objects.all()]
        self.assertEqual(observed, expected)
