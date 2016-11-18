# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from efu.core import Package
from efu.exceptions import UploadError
from efu.utils import CHUNK_SIZE_VAR, SERVER_URL_VAR

from utils import (
    FileFixtureMixin, EnvironmentFixtureMixin, HTTPTestCaseMixin,
    BasePullTestCase, BasePushTestCase, EFUTestCase)


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


class ActiveInactiveTestCase(PackageTestCase):

    def setUp(self):
        self.pkg = Package()
        self.pkg.objects.add_list()
        self.pkg.objects.add_list()

    def test_can_set_active_inactive_backend(self):
        self.pkg.active_inactive_backend = 'u-boot'
        self.assertEqual(self.pkg.active_inactive_backend, 'u-boot')
        self.pkg.active_inactive_backend = 'u-boot'
        self.assertEqual(self.pkg.active_inactive_backend, 'u-boot')

    def test_active_inactive_backend_raises_error_if_invalid_backend(self):
        with self.assertRaises(ValueError):
            self.pkg.active_inactive_backend = 'invalid'

    def test_metadata_with_active_inactive_backend(self):
        self.pkg.active_inactive_backend = 'u-boot'
        metadata = self.pkg.metadata()
        self.assertEqual(metadata['active-backup-backend'], 'u-boot')

    def test_metadata_without_active_inactive_backend(self):
        metadata = self.pkg.metadata()
        self.assertIsNone(metadata.get('active-backup-backend'))


class PackageConstructorsTestCase(PackageTestCase):

    def test_can_create_package_with_default_constructor(self):
        pkg = Package(version=self.version, product=self.product)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)

    def test_can_create_package_from_dumped_file(self):
        fn = self.create_file(json.dumps({
            'product': self.product,
            'version': self.version,
            'supported-hardware': self.supported_hardware,
            'active-backup-backend': 'u-boot',
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'copy',
                        'compressed': False,
                        'options': {
                            'target-device': '/dev/sda',
                            'target-path': '/boot',
                            'filesystem': 'ext4',
                        }
                    }
                ]
            ]
        }))
        pkg = Package.from_file(fn)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.supported_hardware, self.supported_hardware)
        self.assertEqual(pkg.active_inactive_backend, 'u-boot')
        self.assertEqual(len(pkg), 1)
        obj = pkg.objects.get(0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertFalse(obj.compressed)
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.options['target-path'], '/boot')
        self.assertEqual(obj.options['filesystem'], 'ext4')

    def test_can_create_package_from_metadata(self):
        metadata = {
            'product': self.product,
            'version': self.version,
            'active-backup-backend': 'u-boot',
            'objects': [
                [
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
            ]
        }
        pkg = Package.from_metadata(metadata)
        self.assertEqual(pkg.version, self.version)
        self.assertEqual(pkg.product, self.product)
        self.assertEqual(pkg.active_inactive_backend, 'u-boot')
        self.assertEqual(len(pkg), 1)
        obj = pkg.objects.get(0)
        self.assertEqual(obj.filename, self.obj_fn)
        self.assertEqual(obj.mode, 'copy')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.options['target-path'], '/boot')
        self.assertEqual(obj.options['filesystem'], 'ext4')


class PackageWithInstallIfDifferentObjectsTestCase(PackageTestCase):

    def setUp(self):
        super().setUp()
        self.fn = self.create_file(json.dumps({
            'product': '0' * 64,
            'version': '2.0',
            'objects': [
                [
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'options': {
                            'target-device': '/dev/sda',
                            'install-condition': 'always',
                        }
                    },
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'options': {
                            'target-device': '/dev/sda',
                            'install-condition': 'content-diverges'
                        }
                    },
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'options': {
                            'target-device': '/dev/sda',
                            'install-condition': 'version-diverges',
                            'install-condition-pattern-type': 'u-boot',
                        }
                    },
                    {
                        'filename': __file__,
                        'mode': 'raw',
                        'compressed': False,
                        'options': {
                            'target-device': '/dev/sda',
                            'install-condition': 'version-diverges',
                            'install-condition-pattern-type': 'regexp',
                            'install-condition-pattern': '\d+\.\d+',
                        }
                    },
                ]
            ]
        }))
        self.metadata = {
            'product': '0' * 64,
            'version': '2.0',
            'objects': [
                [
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': 'sha256sum'
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': {
                            'version': '0.1',
                            'pattern': 'linux-kernel',
                        }
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': {
                            'version': '0.1',
                            'pattern': {
                                'regexp': '.+',
                                'seek': 100,
                                'buffer-size': 200,
                            },
                        }
                    },
                    {
                        'filename': self.obj_fn,
                        'mode': 'raw',
                        'size': self.obj_size,
                        'sha256sum': self.obj_sha256,
                        'target-device': '/dev/sda',
                        'install-if-different': {
                            'version': '0.1',
                            'pattern': {'regexp': '.+'},
                        }
                    }
                ]
            ]
        }

    def test_can_load_from_file_always_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(0)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(obj.install_condition['install-condition'], 'always')

    def test_can_load_from_file_content_diverges_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(1)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(
            obj.install_condition['install-condition'], 'content-diverges')

    def test_can_load_from_file_known_version_diverges_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(2)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(
            obj.install_condition['install-condition'], 'version-diverges')
        self.assertEqual(
            obj.install_condition['install-condition-pattern-type'], 'u-boot')

    def test_can_load_from_file_custom_version_diverges_object(self):
        pkg = Package.from_file(self.fn)
        obj = pkg.objects.get(3)
        self.assertEqual(obj.filename, __file__)
        self.assertEqual(obj.mode, 'raw')
        self.assertEqual(obj.options['target-device'], '/dev/sda')
        self.assertEqual(
            obj.install_condition['install-condition'], 'version-diverges')
        self.assertEqual(
            obj.install_condition['install-condition-pattern-type'], 'regexp')
        self.assertEqual(
            obj.install_condition['install-condition-pattern'], '\d+\.\d+')

    def test_can_load_from_metadata_always_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(0)
        expected = {'install-condition': 'always'}
        self.assertEqual(obj.install_condition, expected)

    def test_can_load_from_metadata_content_diverges_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(1)
        expected = {'install-condition': 'content-diverges'}
        self.assertEqual(obj.install_condition, expected)

    def test_can_load_from_metadata_known_version_diverges_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(2)
        expected = {
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'linux-kernel',
        }
        self.assertEqual(obj.install_condition, expected)

    def test_can_load_from_metadata_custom_version_diverges_object(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(3)
        expected = {
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'regexp',
            'install-condition-pattern': '.+',
            'install-condition-seek': 100,
            'install-condition-buffer-size': 200,
        }
        self.assertEqual(obj.install_condition, expected)

    def test_can_load_from_metadata_custom_version_object_with_default(self):
        pkg = Package.from_metadata(self.metadata)
        obj = pkg.objects.get(4)
        expected = {
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'regexp',
            'install-condition-pattern': '.+',
            'install-condition-seek': 0,
            'install-condition-buffer-size': -1,
        }
        self.assertEqual(obj.install_condition, expected)


class PackageRepresentationsTestCase(PackageTestCase):

    def test_can_represent_package_as_metadata(self):
        pkg = Package(version=self.version, product=self.product)
        pkg.objects.add_list()
        pkg.objects.add(self.obj_fn, self.obj_mode, self.obj_options)
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
        obj = objects[0][0]
        self.assertEqual(obj['mode'], self.obj_mode)
        self.assertEqual(obj['filename'], self.obj_fn)
        self.assertEqual(obj['size'], self.obj_size)
        self.assertEqual(obj['sha256sum'], self.obj_sha256)
        self.assertEqual(obj['target-device'], '/dev/sda')

    def test_can_represent_package_as_template(self):
        pkg = Package(version=self.version, product=self.product)
        pkg.objects.add_list()
        obj = pkg.objects.add(self.obj_fn, self.obj_mode, self.obj_options)
        expected_obj_template = obj.template()
        pkg.add_supported_hardware(
            name=self.hardware, revisions=self.hardware_revision)
        template = pkg.template()
        self.assertEqual(template['version'], self.version)
        self.assertEqual(template['product'], self.product)
        self.assertEqual(len(template['objects']), 1)
        self.assertEqual(
            template['supported-hardware'], self.supported_hardware)
        objects = template['objects'][0]
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], expected_obj_template)

    def test_can_represent_package_as_file(self):
        dest = '/tmp/efu-dump.json'
        self.addCleanup(self.remove_file, dest)
        pkg = Package(version=self.version, product=self.product)
        pkg.objects.add_list()
        obj = pkg.objects.add(self.obj_fn, self.obj_mode, self.obj_options)
        expected_obj_dump = obj.template()
        self.assertFalse(os.path.exists(dest))
        pkg.dump(dest)
        self.assertTrue(os.path.exists(dest))
        with open(dest) as fp:
            dump = json.load(fp)
        self.assertEqual(dump['version'], self.version)
        self.assertEqual(dump['product'], self.product)
        self.assertEqual(len(dump['objects']), 1)
        dump_obj = dump['objects'][0][0]
        self.assertEqual(dump_obj, expected_obj_dump)

    def test_can_represent_package_as_string(self):
        cwd = os.getcwd()
        os.chdir('tests/fixtures/package')
        self.addCleanup(os.chdir, cwd)
        with open('package_full.txt') as fp:
            expected = fp.read()
        package = Package(
            version='2.0',
            product='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')  # nopep8
        package.objects.add_list()
        package.objects.add('files/pkg.json', mode='raw', options={
            'target-device': '/dev/sda',
            'chunk-size': 1234,
            'skip': 0,
            'count': -1
        })
        package.objects.add('files/setup.py', mode='raw', options={
            'target-device': '/dev/sda',
            'seek': 5,
            'truncate': True,
            'chunk-size': 10000,
            'skip': 19,
            'count': 3
        })
        package.objects.add('files/tox.ini', mode='copy', options={
            'target-device': '/dev/sda3',
            'target-path': '/dev/null',
            'filesystem': 'ext4',
            'format?': True,
            'format-options': '-i 100 -J size=500',
            'mount-options': '--all --fstab=/etc/fstab2'
        })
        package.objects.add('files/archive.tar.gz', mode='tarball', options={
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


class PackagePullTestCase(BasePullTestCase):

    def test_can_download_metadata(self):
        metadata = self.package.download_metadata()
        self.assertEqual(metadata, self.metadata)

    def test_get_metadata_raises_error_when_metadata_does_not_exist(self):
        self.httpd.register_response(
            '/products/{}/packages/{}'.format(self.product, self.pkg_uid),
            'GET', status_code=404)
        with self.assertRaises(ValueError):
            self.package.download_metadata()

    def test_get_download_list_returns_empty_list_with_identical_file(self):
        with open(self.obj_fn, 'bw') as fp:
            fp.write(self.obj_content)
        package = Package.from_metadata(self.metadata)
        objects = package.get_download_list()
        self.assertTrue(os.path.exists(self.obj_fn))
        self.assertEqual(len(objects), 0)

    def test_get_download_list_returns_objects_when_file_does_not_exists(self):
        package = Package.from_metadata(self.metadata)
        objects = package.get_download_list()
        self.assertFalse(os.path.exists(self.obj_fn))
        self.assertEqual(len(objects), 1)

    def test_get_download_list_raises_error_when_existent_file_diverges(self):
        content = 'overwrited'
        with open(self.obj_fn, 'w') as fp:
            fp.write(content)
        package = Package.from_metadata(self.metadata)
        with self.assertRaises(FileExistsError):
            package.get_download_list()
        with open(self.obj_fn) as fp:
            self.assertEqual(fp.read(), content)

    def test_pull_raises_error_when_objects_diverges(self):
        with open(self.obj_fn, 'w') as fp:
            fp.write('overwritten')
        with self.assertRaises(FileExistsError):
            self.package.pull(full=True)

    def test_pull_downloads_files_if_full_is_True(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        self.package.pull(full=True)
        self.assertTrue(os.path.exists(self.obj_fn))

    def test_pull_does_not_download_files_if_full_is_False(self):
        self.assertFalse(os.path.exists(self.obj_fn))
        self.package.pull(full=False)
        self.assertFalse(os.path.exists(self.obj_fn))


class PushTestCase(BasePushTestCase):

    def test_upload_metadata_returns_None_when_successful(self):
        self.start_push_url(self.product, self.package_uid)
        self.package.load()
        observed = self.package.upload_metadata()
        self.assertIsNone(observed)

    def test_upload_metadata_raises_exception_when_fail(self):
        self.start_push_url(self.product, self.package_uid, success=False)
        self.package.load()
        with self.assertRaises(UploadError):
            self.package.upload_metadata()

    def test_upload_metadata_request_is_made_correctly(self):
        self.start_push_url(self.product, self.package_uid)
        start_url = self.httpd.url(
            '/products/{}/packages'.format(self.product))
        self.package.load()
        self.package.upload_metadata()

        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, start_url)
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        metadata = json.loads(request.body.decode())
        self.assertEqual(metadata, self.package.metadata())

    def test_upload_metadata_updates_package_uid(self):
        self.start_push_url(self.product, self.package_uid)
        self.package.load()
        self.assertIsNone(self.package.uid)
        self.package.upload_metadata()
        self.assertEqual(self.package.uid, self.package_uid)

    def test_finish_push_returns_None_when_successful(self):
        self.package.uid = self.package_uid
        self.finish_push_url(self.product, self.package.uid)
        self.assertIsNone(self.package.finish_push())

    def test_finish_push_raises_error_when_fail(self):
        self.package.uid = self.package_uid
        self.finish_push_url(self.product, self.package_uid, success=False)
        with self.assertRaises(UploadError):
            self.package.finish_push()

    def test_finish_push_request_is_made_correctly(self):
        self.finish_push_url(self.product, self.package_uid, success=True)
        path = '/products/{}/packages/{}/finish'.format(
            self.product, self.package_uid)
        url = self.httpd.url(path)
        self.package.uid = self.package_uid
        self.package.finish_push()
        request = self.httpd.requests[0]
        self.assertEqual(len(self.httpd.requests), 1)
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url, url)
        self.assertEqual(request.body, b'')

    def test_upload_objects_return_None_when_successful(self):
        self.set_push(self.package, self.package_uid)
        self.package.upload_metadata()
        observed = self.package.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_return_None_when_file_exists(self):
        self.set_push(self.package, self.package_uid, upload_exists=True)

        self.package.upload_metadata()
        observed = self.package.upload_objects()
        self.assertIsNone(observed)

    def test_upload_objects_requests_are_made_correctly(self):
        self.set_push(self.package, self.package_uid)
        self.package.upload_metadata()
        self.package.upload_objects()
        self.package.finish_push()
        # 1 request for starting push
        # 3 * (2 requests per file [get url and upload])
        # 1 request for finishing push
        # Total: 8 requests
        self.assertEqual(len(self.httpd.requests), 8)
