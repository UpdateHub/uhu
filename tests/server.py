# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import signal
import sys
from itertools import count

from efu.core import Package
from efu.utils import LOCAL_CONFIG_VAR, CHUNK_SIZE_VAR

from tests.utils import (
    PushFixtureMixin, HTTPTestCaseMixin, EFUTestCase,
    FileFixtureMixin, EnvironmentFixtureMixin, UploadFixtureMixin)


product_uid = count()


def push_cmd(cmd):
    product = ''.rjust(64, str(next(product_uid)))
    name = ' '.join(cmd.__name__.split('_')).upper()

    def wrapped(self):
        pkg_fn = self.create_file('')
        self.set_env_var(LOCAL_CONFIG_VAR, pkg_fn)
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        pkg = Package(version='1', product=product)
        pkg.objects.add_list()
        for _ in range(3):
            fn = self.create_file('spam')
            pkg.objects.add(fn, 'raw', {'target-device': '/'})
        pkg.dump(pkg_fn)
        kwargs = cmd(self)
        self.set_push(pkg, '100',  **kwargs)
        print('- {}:\nexport {}={}\n'.format(name, LOCAL_CONFIG_VAR, pkg_fn))
    return wrapped


class EFUTestServer(PushFixtureMixin, FileFixtureMixin, UploadFixtureMixin,
                    EnvironmentFixtureMixin, HTTPTestCaseMixin, EFUTestCase):

    def __init__(self):
        self.start_server(simulate_application=True)
        super().__init__()
        signal.signal(signal.SIGINT, self.shutdown)

    @push_cmd
    def push_success(self):
        return {}

    @push_cmd
    def push_existent(self):
        return {'upload_exists': True}

    @push_cmd
    def push_finish_push_fail(self):
        return {'finish_success': False}

    def shutdown(self, *args):
        print('Shutting down server...')
        self.clean()
        EFUTestServer.stop_server()

    def main(self):
        print('EFU test server\n')
        print('export EFU_SERVER_URL={}'.format(self.httpd.url('')))
        print('export EFU_CHUNK_SIZE=1')
        print()
        self.push_success()
        self.push_existent()
        self.push_finish_push_fail()


if __name__ == '__main__':
    sys.exit(EFUTestServer().main())
