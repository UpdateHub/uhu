# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import signal
import sys

from efu.push.package import Package
from efu.push.file import File

from tests.base import PushMockMixin


class EFUTestServer(PushMockMixin):

    def __init__(self):
        EFUTestServer.start_server(simulate_application=True)
        super().__init__()
        signal.signal(signal.SIGINT, self.shutdown)
        self.cmd = '- {}:\nefu push {}'

    def cmd_success(self):
        pkg = Package(self.create_package_file(1, self.fns))
        uploads = self.create_uploads_meta(pkg.files.values())
        self.set_push(1, uploads=uploads)
        print(self.cmd.format('SUCCESS', pkg.file))
        File._File__reset_id_generator()

    def cmd_existent(self):
        pkg = Package(self.create_package_file(2, self.fns))
        uploads = self.create_uploads_meta(
            pkg.files.values(), file_exists=True)
        self.set_push(2, uploads=uploads)
        print(self.cmd.format('EXISTENT', pkg.file))
        File._File__reset_id_generator()

    def cmd_finish_push_fail(self):
        pkg = Package(self.create_package_file(3, self.fns))
        uploads = self.create_uploads_meta(pkg.files.values())
        self.set_push(3, uploads=uploads, finish_success=False)
        print(self.cmd.format('FINISH FAIL', pkg.file))
        File._File__reset_id_generator()

    def cmd_file_part_fail(self):
        pkg = Package(self.create_package_file(4, self.fns))
        uploads = self.create_uploads_meta(pkg.files.values(), success=False)
        self.set_push(4, uploads=uploads)
        print(self.cmd.format('FILE PART FAIL', pkg.file))
        File._File__reset_id_generator()

    def cmd_mixed(self):
        pkg = Package(self.create_package_file(5, self.fns))
        f1, f2, f3 = list(pkg.files.values())
        u1 = self.create_upload_meta(f1)
        u2 = self.create_upload_meta(f2, success=False)
        u3 = self.create_upload_meta(f3, file_exists=True)
        uploads = [u1, u2, u3]
        self.set_push(5, uploads=uploads)
        print(self.cmd.format('MIXED', pkg.file))
        File._File__reset_id_generator()

    def shutdown(self, *args):
        print('Shutting down server...')
        self.clean()
        EFUTestServer.stop_server()

    def main(self):
        print('EFU test server\n')
        print('export EFU_SERVER_URL={}'.format(self.httpd.url('')))
        print('export EFU_CHUNK_SIZE=1')
        self.cmd_success()
        self.cmd_existent()
        self.cmd_finish_push_fail()
        self.cmd_file_part_fail()
        self.cmd_mixed()


if __name__ == '__main__':
    sys.exit(EFUTestServer().main())
