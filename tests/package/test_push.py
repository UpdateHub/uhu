# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest
from unittest.mock import patch

from uhu.core.package import Package


class PackagePushTestCase(unittest.TestCase):

    @patch('uhu.core.package.push_package', return_value='42')
    def test_push_sets_package_uid_when_successful(self, mock):
        pkg = Package()
        uid = pkg.push()
        self.assertEqual(pkg.uid, '42')
        self.assertEqual(uid, '42')
