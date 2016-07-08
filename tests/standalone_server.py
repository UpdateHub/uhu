# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import signal
import sys
from itertools import count

from tests.base import ServerMocker
from tests.httpmock.httpd import HTTPMockServer


class EFUTestServer(object):

    def __init__(self):
        signal.signal(signal.SIGINT, self.shutdown)

        self.server = HTTPMockServer(simulate_application=True)
        self.fixture = ServerMocker(self.server)
        self.fixture.set_server_url()

    def print_commands(self):
        cmd = '{}: efu upload {}'
        product_id = count()

        success = self.fixture.set_transaction(
            next(product_id), file_size=5, success_files=2)

        existent_files = self.fixture.set_transaction(
            next(product_id), file_size=5,
            existent_files=2, success_files=0)

        start_transaction_fail = self.fixture.set_transaction(
            next(product_id), file_size=5, start_success=False)

        finish_transaction_fail = self.fixture.set_transaction(
            next(product_id), file_size=5, finish_success=False)

        part_file_fail = self.fixture.set_transaction(
            next(product_id), file_size=5,
            part_fail_files=2, success_files=0)

        # Random output
        mix = self.fixture.set_transaction(
            next(product_id), file_size=5,
            success_files=1, part_fail_files=1, existent_files=1)

        print(cmd.format('SUCCESS', success))
        print(cmd.format('EXISTENT FILES', existent_files))
        print(cmd.format('START TRANSACTION FAIL', start_transaction_fail))
        print(cmd.format('FINISH TRANSACTION FAIL', finish_transaction_fail))
        print(cmd.format('PART FILE FAIL', part_file_fail))
        print(cmd.format('MIX', mix))

    def main(self):
        print('EFU test server\n')
        print('EXPORT COMMAND: export EFU_SERVER_URL={}'.format(
            self.server.url('')
        ))
        print()
        self.print_commands()
        self.server.start()

    def shutdown(self, *args):
        print()
        print('Shutting down server...')
        self.server.shutdown()
        self.fixture.clean_generated_files()


if __name__ == '__main__':
    server = EFUTestServer()
    sys.exit(server.main())
