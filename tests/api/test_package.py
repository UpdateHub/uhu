# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from efu.core import Package
from efu.utils import CHUNK_SIZE_VAR, SERVER_URL_VAR

from ..utils import (FileFixtureMixin, EnvironmentFixtureMixin,
                     HTTPTestCaseMixin, EFUTestCase)


class PackageTestCase(FileFixtureMixin, EnvironmentFixtureMixin, EFUTestCase):

    def setUp(self):
        self.set_env_var(CHUNK_SIZE_VAR, 2)
        self.version = '2.0'
        self.product = '1234'
        self.hardware = 'PowerX'
        self.hardware_revision = ['PX230']
        self.supported_hardware = {
            self.hardware: {
                'name': self.hardware,
                'revisions': self.hardware_revision,
            }
        }
        self.pkg_uid = 'pkg-uid'
        self.obj_content = b'spam'
        self.obj_fn = self.create_file(self.obj_content)
        self.obj_sha256 = self.sha256sum(self.obj_content)
        self.obj_mode = 'raw'
        self.obj_options = {'target-device': '/dev/sda'}
        self.obj_size = 4


class PackageConstructorsTestCase(PackageTestCase):

    def test_can_create_package_with_default_constructor(self):
        pkg = Package(version=self.version, product=self.product)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)

    def test_can_create_package_from_dumped_file(self):
        obj_id = 23
        fn = self.create_file(json.dumps({
            'product': self.product,
            'version': self.version,
            'supported-hardware': self.supported_hardware,
            'objects': {
                obj_id: {
                    'filename': self.obj_fn,
                    'mode': 'copy',
                    'options': {
                        'target-device': '/dev/sda',
                        'target-path': '/boot',
                        'filesystem': 'ext4',
                    }
                }
            }
        }))
        pkg = Package.from_file(fn)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.supported_hardware, self.supported_hardware)
        self.assertEqual(len(pkg), 1)
        obj = pkg.objects[obj_id]
        self.assertEqual(obj.uid, obj_id)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.options['target-path'], '/boot')
        self.assertEqual(obj.options['filesystem'], 'ext4')

    def test_can_create_package_from_metadata(self):
        metadata = {
            'product': self.product,
            'version': self.version,
            'objects': [
                {
                    'filename': self.obj_fn,
                    'mode': 'copy',
                    'size': self.obj_size,
                    'sha256sum': self.obj_sha256,
                    'target-device': '/dev/sda',
                    'target-path': '/boot',
                    'filesystem': 'ext4'
                }
            ]
        }
        pkg = Package.from_metadata(metadata)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(len(pkg), 1)
        obj = pkg.objects[1]
        self.assertEqual(obj.uid, 1)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.options['target-path'], '/boot')
        self.assertEqual(obj.options['filesystem'], 'ext4')


class PackageObjectManagementTestCase(PackageTestCase):

    def test_can_add_object(self):
        pkg = Package(version=self.version, product=self.product)
        self.assertEqual(len(pkg), 0)
        obj = pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        self.assertEqual(len(pkg), 1)
        self.assertEqual(obj.uid, 1)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.options['target-device'], '/dev/sda')

    def test_can_add_more_than_one_object_per_file(self):
        pkg = Package(version=self.version, product=self.product)
        self.assertEqual(len(pkg), 0)
        obj1 = pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        obj2 = pkg.add_object(
            self.obj_fn, self.obj_mode, {'target-device': '/dev/sdb'})
        self.assertEqual(len(pkg), 2)
        self.assertNotEqual(obj1.uid, obj2.uid)
        self.assertEqual(obj1.filename, obj2.filename)
        self.assertEqual(obj1.options['target-device'], '/dev/sda')
        self.assertEqual(obj2.options['target-device'], '/dev/sdb')

    def test_can_edit_object(self):
        pkg = Package(version=self.version, product=self.product)
        obj = pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        pkg.edit_object(obj.uid, 'target-device', '/dev/sdb')
        self.assertEqual(obj.options['target-device'], '/dev/sdb')

    def test_edit_object_raises_error_if_object_doesnt_exist(self):
        pkg = Package(version=self.version, product=self.product)
        with self.assertRaises(ValueError):
            pkg.edit_object(100, 'target-device', '/dev/sdb')

    def test_edit_object_raises_error_if_invalid_value_is_passed(self):
        pkg = Package(version=self.version, product=self.product)
        obj = pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        with self.assertRaises(ValueError):
            pkg.edit_object(obj.uid, 'target-device', 1)  # should be a path

    def test_edit_object_raises_error_if_invalid_option_is_passed(self):
        pkg = Package(version=self.version, product=self.product)
        obj = pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        with self.assertRaises(ValueError):
            pkg.edit_object(obj.uid, 'target-path', '/')  # bot allowed in raw

    def test_can_remove_object(self):
        pkg = Package(version=self.version, product=self.product)
        obj = pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        self.assertEqual(len(pkg), 1)
        pkg.remove_object(obj.uid)
        self.assertEqual(len(pkg), 0)

    def test_remove_object_raises_error_if_invalid_file(self):
        pkg = Package(version=self.version, product=self.product)
        with self.assertRaises(ValueError):
            pkg.remove_object('invalid')


class PackageRepresentationsTestCase(PackageTestCase):

    def test_can_represent_package_as_metadata(self):
        pkg = Package(version=self.version, product=self.product)
        pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        pkg.add_supported_hardware(
            name=self.hardware, revisions=self.hardware_revision)
        pkg.load()
        metadata = pkg.metadata()
        self.assertEqual(metadata['version'], self.version)
        self.assertEqual(metadata['product'], self.product)
        self.assertEqual(
            metadata['supported-hardware'], self.supported_hardware)
        objects = metadata['objects']
        self.assertEqual(len(objects), 1)
        obj = objects[0]
        self.assertEqual(obj['mode'], self.obj_mode)
        self.assertEqual(obj['filename'], self.obj_fn)
        self.assertEqual(obj['size'], self.obj_size)
        self.assertEqual(obj['sha256sum'], self.obj_sha256)
        self.assertEqual(obj['target-device'], '/dev/sda')

    def test_can_represent_package_as_template(self):
        pkg = Package(version=self.version, product=self.product)
        pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        pkg.add_supported_hardware(
            name=self.hardware, revisions=self.hardware_revision)
        template = pkg.template()
        self.assertEqual(template['version'], self.version)
        self.assertEqual(template['product'], self.product)
        self.assertEqual(len(template['objects']), 1)
        self.assertEqual(
            template['supported-hardware'], self.supported_hardware)
        template_obj = template['objects'][1]
        self.assertEqual(template_obj['mode'], self.obj_mode)
        self.assertEqual(template_obj['filename'], self.obj_fn)
        self.assertEqual(template_obj['options'], self.obj_options)

    def test_can_represent_package_as_file(self):
        dest = '/tmp/efu-dump.json'
        self.addCleanup(self.remove_file, dest)
        pkg = Package(version=self.version, product=self.product)
        pkg.add_object(self.obj_fn, self.obj_mode, self.obj_options)
        self.assertFalse(os.path.exists(dest))
        pkg.dump(dest)
        self.assertTrue(os.path.exists(dest))
        with open(dest) as fp:
            dump = json.load(fp)
        self.assertEqual(dump['version'], self.version)
        self.assertEqual(dump['product'], self.product)
        self.assertEqual(len(dump['objects']), 1)
        dump_obj = dump['objects']['1']
        self.assertEqual(dump_obj['mode'], self.obj_mode)
        self.assertEqual(dump_obj['filename'], self.obj_fn)
        self.assertEqual(dump_obj['options'], self.obj_options)

    def test_can_represent_package_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures')
        self.addCleanup(os.chdir, cwd)
        with open('local_config.txt') as fp:
            expected = fp.read().strip()
        package = Package(
            version='2.0',
            product='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')  # nopep8
        package.add_object('files/pkg.json', mode='raw', options={
            'target-device': '/dev/sda',
            'chunk-size': 1234,
            'skip': 0,
            'count': -1
        })
        package.add_object('files/setup.py', mode='raw', options={
            'target-device': '/dev/sda',
            'seek': 5,
            'truncate': True,
            'chunk-size': 10000,
            'skip': 19,
            'count': 3
        })
        package.add_object('files/tox.ini', mode='copy', options={
            'compressed': True,
            'required-uncompressed-size': 345,
            'target-device': '/dev/sda3',
            'target-path': '/dev/null',
            'filesystem': 'ext4',
            'format?': True,
            'format-options': '-i 100 -J size=500',
            'mount-options': '--all --fstab=/etc/fstab2'
        })
        observed = str(package)
        self.assertEqual(observed, expected)

    def test_package_as_string_when_empty(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures')
        self.addCleanup(os.chdir, cwd)
        pkg = Package()
        observed = str(pkg)
        with open('local_empty_config.txt') as fp:
            expected = fp.read().strip()
        self.assertEqual(observed, expected)


class PackageStatusTestCase(HTTPTestCaseMixin, PackageTestCase):

    def setUp(self):
        super().setUp()
        self.set_env_var(SERVER_URL_VAR, self.httpd.url(''))

    def test_can_get_a_package_status(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.pkg_uid)
        package = Package(product=self.product, uid=self.pkg_uid)
        expected = 'finished'
        self.httpd.register_response(
            path, status_code=200, body=json.dumps({'status': expected}))
        observed = package.get_status()
        self.assertEqual(observed, expected)

    def test_get_package_status_raises_error_if_package_doesnt_exist(self):
        path = '/products/{}/packages/{}/status'.format(
            self.product, self.pkg_uid)
        self.httpd.register_response(path, status_code=404)
        package = Package(product=self.product, uid=self.pkg_uid)
        with self.assertRaises(ValueError):
            package.get_status()


class PackageSupportedHardwareManagementTestCase(PackageTestCase):

    def test_can_add_supported_hardware(self):
        pkg = Package()
        self.assertEqual(len(pkg.supported_hardware), 0)
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        self.assertEqual(len(pkg.supported_hardware), 1)
        hardware = pkg.supported_hardware['PowerX']
        self.assertEqual(hardware['name'], 'PowerX')
        self.assertEqual(hardware['revisions'], ['PX230'])

    def test_can_remove_supported_hardware(self):
        pkg = Package()
        pkg.add_supported_hardware(name='PowerX')
        pkg.add_supported_hardware(name='PowerY')
        self.assertEqual(len(pkg.supported_hardware), 2)
        pkg.remove_supported_hardware('PowerX')
        self.assertEqual(len(pkg.supported_hardware), 1)
        pkg.remove_supported_hardware('PowerY')
        self.assertEqual(len(pkg.supported_hardware), 0)

    def test_remove_supported_hardware_raises_error_if_invalid_hardware(self):
        pkg = Package()
        with self.assertRaises(ValueError):
            pkg.remove_supported_hardware('dosnt-exist')

    def test_can_add_hardware_revision(self):
        pkg = Package()
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        pkg.add_supported_hardware_revision('PowerX', 'PX240')
        revisions = pkg.supported_hardware['PowerX']['revisions']
        self.assertEqual(revisions, ['PX230', 'PX240'])

    def test_add_hardware_revision_raises_error_if_invalid_hardware(self):
        pkg = Package()
        with self.assertRaises(ValueError):
            pkg.add_supported_hardware_revision('dosnt-exist', 'revision')

    def test_can_remove_hardware_revision(self):
        pkg = Package()
        pkg.add_supported_hardware(name='PowerX', revisions=['PX240'])
        self.assertEqual(len(pkg.supported_hardware['PowerX']['revisions']), 1)
        pkg.remove_supported_hardware_revision('PowerX', 'PX240')
        self.assertEqual(len(pkg.supported_hardware['PowerX']['revisions']), 0)

    def test_remove_hardware_revision_raises_error_if_invalid_hardware(self):
        pkg = Package()
        with self.assertRaises(ValueError):
            pkg.remove_supported_hardware_revision('dosnt-exist', 'revision')

    def test_remove_hardware_revision_raises_error_if_invalid_revision(self):
        pkg = Package()
        pkg.add_supported_hardware('PowerX')
        with self.assertRaises(ValueError):
            pkg.remove_supported_hardware_revision('PowerX', 'dosnt-exist')

    def test_hardware_revisions_are_alphanumeric_sorted(self):
        pkg = Package()
        pkg.add_supported_hardware(name='PowerX', revisions=['PX240'])
        pkg.add_supported_hardware_revision('PowerX', 'PX250')
        pkg.add_supported_hardware_revision('PowerX', 'PX230')
        expected = ['PX230', 'PX240', 'PX250']
        observed = pkg.supported_hardware['PowerX']['revisions']
        self.assertEqual(observed, expected)

    def test_entries_are_not_duplicated_when_adding_same_hardware_twice(self):
        pkg = Package()
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        self.assertEqual(len(pkg.supported_hardware), 1)
        self.assertEqual(len(pkg.supported_hardware['PowerX']['revisions']), 1)

    def test_dump_package_with_supported_hardware(self):
        pkg = Package()
        pkg.add_supported_hardware(name='PowerX', revisions=['PX230'])
        pkg_fn = self.create_file('')
        pkg.dump(pkg_fn)
        with open(pkg_fn) as fp:
            dump = json.load(fp)
        supported_hardware = dump.get('supported-hardware')
        self.assertIsNotNone(supported_hardware)
        self.assertEqual(len(supported_hardware), 1)
        self.assertEqual(supported_hardware['PowerX']['name'], 'PowerX')
        self.assertEqual(supported_hardware['PowerX']['revisions'], ['PX230'])

    def test_supported_hardware_within_package_string(self):
        pkg = Package(version='2.0', product='1234')
        pkg.add_supported_hardware(name='PowerX')
        pkg.add_supported_hardware(name='PowerY', revisions=['PY230'])
        pkg.add_supported_hardware(
            name='PowerZ', revisions=['PZ250', 'PZ240', 'PZ230'])
        observed = str(pkg)
        with open('tests/fixtures/supported_hardware.txt') as fp:
            expected = fp.read().strip()
        self.assertEqual(observed, expected)
