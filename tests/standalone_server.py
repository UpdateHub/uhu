# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import signal
import sys
from itertools import count

from efu.package import Package
from efu.package import File

from tests.base import PushMockMixin, PullMockMixin


product_id = count()


def push_cmd(cmd):
    id_ = next(product_id)
    name = ' '.join(cmd.__name__.split('_')).upper()

    def wrapped(self):
        pkg_fn = self.create_package_file(id_, self.fns)
        os.environ['EFU_PACKAGE_FILE'] = pkg_fn
        pkg = Package('')
        kwargs = cmd(self, pkg)
        self.set_push(id_, **kwargs)
        print('- {}:\nexport EFU_PACKAGE_FILE={}\n'.format(name, pkg.file))
        File._File__reset_id_generator()

    return wrapped


class EFUTestServer(PushMockMixin, PullMockMixin):

    def __init__(self):
        EFUTestServer.start_server(simulate_application=True)
        super().__init__()
        signal.signal(signal.SIGINT, self.shutdown)

    @push_cmd
    def push_success(self, pkg):
        return {'uploads': self.create_uploads_meta(pkg.files.values())}

    @push_cmd
    def push_existent(self, pkg):
        uploads = self.create_uploads_meta(
            pkg.files.values(), file_exists=True)
        return {'uploads': uploads}

    @push_cmd
    def push_finish_push_fail(self, pkg):
        uploads = self.create_uploads_meta(pkg.files.values())
        return {'uploads': uploads, 'finish_success': False}

    @push_cmd
    def push_file_part_fail(self, pkg):
        uploads = self.create_uploads_meta(pkg.files.values(), success=False)
        return {'uploads': uploads}

    @push_cmd
    def push_mixed(self, pkg):
        f1, f2, f3 = list(pkg.files.values())
        u1 = self.create_upload_meta(f1)
        u2 = self.create_upload_meta(f2, success=False)
        u3 = self.create_upload_meta(f3, file_exists=True)
        return {'uploads': [u1, u2, u3]}

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
        self.push_file_part_fail()
        self.push_mixed()


if __name__ == '__main__':
    sys.exit(EFUTestServer().main())
