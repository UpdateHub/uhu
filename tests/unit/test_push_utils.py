# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from efu.push.exceptions import CommitDoesNotExist
from efu.push.utils import get_commit_status

from ..base import EFUTestCase


class PushUtilsTestCase(EFUTestCase):

    def test_can_get_a_commit_status(self):
        expected = 'finished'
        self.httpd.register_response(
            '/products/{}/commits/1234/status'.format(self.product_id),
            status_code=200,
            body=json.dumps({'status': expected})
        )
        observed = get_commit_status('1234')
        self.assertEqual(observed, expected)

    def test_get_commit_status_raises_error_if_commit_doesnt_exist(self):
        self.httpd.register_response(
            '/products/{}/commits/1234/status'.format(self.product_id),
            status_code=404,
        )
        with self.assertRaises(CommitDoesNotExist):
            get_commit_status('1234')
